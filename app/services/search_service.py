# app/services/search_service.py
from decimal import Decimal
from uuid import UUID
from typing import Iterable, Sequence

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from models.document import Document
from models.query import Query, QueryJobStatus
from models.query_result_item import QueryResultItem
from models.user import User
from models.transaction import Transaction, TransactionType

from services.transaction_service import TransactionService
from services.index_service import IndexService
from services.exceptions import UserNotExistsException, AccessDeniedException, QueryNotFoundException

from dataclasses import dataclass
@dataclass(frozen=True)
class QueryResults:
    query_id: UUID
    query: Query
    items: tuple["QueryResultItemDTO", ...]

@dataclass(frozen=True)
class QueryResultItemDTO:
    document_id: UUID
    document_title: str
    score: float
    rank: int

class SearchService:
    """
    Сервис поиска
    """

    def __init__(
        self,
        session: Session,
        transaction_service: TransactionService,
        index_service: IndexService,
        search_cost: Decimal = Decimal("1.00"),
    ):
        self._session = session
        self._transaction_service = transaction_service
        self._index_service = index_service
        self._search_cost = search_cost

    def create_query_job(self, user_id: UUID, query_text: str, top_k: int) -> UUID:
        """
        Поставить в очередь задание на поиск. Вызывается из API
        Данный метод уже должен проверить кредит, списать его, если достаточно - поставить задачу в очередь.
        """  

        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        # 1) создаём Query
        query = Query(
            user_id=str(user_id),
            query_text=query_text,
            cost=self._search_cost,
            transaction_id=None,
            top_k=top_k
        )
        self._session.add(query)
        self._session.flush()

        # 2) списываем кредит
        transaction_id = self._transaction_service.withdraw_credit(user_id, self._search_cost, reason=TransactionType.SEARCH_QUERY, reference_id=UUID(query.id))

        # 3) обновляем транзакцию: reason + reference_id = query.id
        transaction = self._session.get(Transaction, str(transaction_id))
        if transaction is not None:
            transaction.reason = TransactionType.SEARCH_QUERY.value
            transaction.reference_id = query.id
            self._session.add(transaction)
            self._session.flush()

        # 4) связываем query с transaction
        query.transaction_id = str(transaction_id)
        self._session.add(query)
        self._session.flush()
        
        self._session.commit()

        return UUID(query.id)
    
    def process_query_job(self, query_id: UUID) -> None:
        """
        Выполнить задание на поиск.
        Вызывается из воркера.        
        Вернуть top_k совпадений, посчитать эмбеддинги для текста запроса, отправить запрос на поиск похожего, сгенерировать ответ...
        В общем, самый важный метод сервиса, ради которого всё и затевается
        """        

        query = self._session.get(Query, str(query_id))
        if query is None:
            return

        if query.query_status == QueryJobStatus.DONE.value:
            return

        try:
            user_id = UUID(query.user_id)

            top_k = query.top_k

            # 5) поиск через индекс (VectorIndex внутри IndexService)
            hits = self._index_service.search(user_id, query.query_text, top_k)

            # подчистим старые результаты (при retry Celery обязательно)
            self._session.execute(
                delete(QueryResultItem).where(QueryResultItem.query_id == query.id)
            )

            ordered_docs: list[tuple[Document, float]] = []
            if hits:
                hit_ids = [str(doc_id) for (doc_id, _s) in hits]
                # Подтягиваем документы одним запросом
                docs = list(
                    self._session.execute(
                        select(Document).where(Document.id.in_(hit_ids))
                    ).scalars().all()
                )
                docs_by_id = {d.id: d for d in docs}

                # Восстанавливаем порядок как в hits + фильтруем те, которых нет/не принадлежат пользователю
                for (doc_id, score) in hits:
                    d = docs_by_id.get(str(doc_id))
                    if d is None:
                        continue
                    if d.owner_id != str(user_id):
                        continue
                    ordered_docs.append((d, float(score)))
            
            # 6) пишем QueryResultItem в БД (для истории история)
            for rank, (doc, score) in enumerate(ordered_docs, start=1):
                self._session.add(
                    QueryResultItem(
                        query_id=query.id,
                        document_id=doc.id,
                        score=score,
                        rank=rank,
                    )
                )

            query.query_status = QueryJobStatus.DONE.value
            self._session.add(query)
            self._session.flush()

        except Exception as e:
            query.query_status = QueryJobStatus.FAILED.value
            query.query_error = str(e)[:1000]

            self._session.add(query)
            self._session.flush()
            raise

    def search_documents(self, query_id : UUID) -> list[Document]:
        """Вернуть документы по поиску"""
        query = (
            select(Document)
            .join(QueryResultItem, QueryResultItem.document_id == Document.id)
            .where(QueryResultItem.query_id == str(query_id))
            .order_by(QueryResultItem.rank.asc())
        )
        return list(self._session.execute(query).scalars().all())
    
    def get_query(self, query_id: UUID, limit: int = 50, offset: int = 0) -> Sequence[Query]:
        """Вернуть search query."""
        query = (
            select(Query)
            .where(Query.id == str(query_id))
        )
        return self._session.execute(query).scalars().all()

    def get_query_results(
        self,
        user_id: UUID,
        query_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> QueryResults:
        """
        Получить Query + результаты из БД.
        Если query ещё не обработан воркером — items будет пустой tuple.
        """
        q = self._session.get(Query, str(query_id))
        if q is None:
            raise QueryNotFoundException()

        if q.user_id != str(user_id):
            raise AccessDeniedException()


        self._session.refresh(q)

        # Читаем результаты (если их ещё нет — вернётся пусто)
        items_stmt = (
            select(QueryResultItem, Document.title.label("document_title"))
            .join(Document, Document.id == QueryResultItem.document_id)
            .where(QueryResultItem.query_id == q.id)
            .order_by(QueryResultItem.rank.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self._session.execute(items_stmt).all())

        dto_items = tuple(
            QueryResultItemDTO(
                document_id=UUID(row[0].document_id),
                document_title=row[1],
                score=float(row[0].score),
                rank=int(row[0].rank)
            )
            for row in rows
        )

        return QueryResults(query_id=UUID(q.id), items=dto_items, query=q)

    def get_history(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[QueryResults]:
        """Вернуть историю запросов пользователя."""
        itemsQuery = (
            select(Query)
            .where(Query.user_id == str(user_id))
            .order_by(Query.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        queries = list(self._session.execute(itemsQuery).scalars().all())

        results: list[QueryResults] = []
        for q in queries:
            itemsQuery = (
                select(QueryResultItem, Document.title.label("document_title"))
                .join(Document, Document.id == QueryResultItem.document_id)
                .where(QueryResultItem.query_id == q.id)
                .order_by(QueryResultItem.rank.asc())
            )
            rows = list(self._session.execute(itemsQuery).all())
            dto_items = tuple(
                QueryResultItemDTO(document_id=UUID(row[0].document_id), document_title=row[1], score=float(row[0].score), rank=int(row[0].rank))
                for row in rows
            )
            results.append(QueryResults(query_id=UUID(q.id), items=dto_items, query=q))
        return results

    def clear_history(self, user_id: UUID) -> None:
        """Очистить историю запросов пользователя."""
        # удаляем запросы пользователя; 
        # результаты удалятся каскадом (через FK и настройки),
        # на всякий случай чистим явным delete по QueryResultItem тож проходимся (мало ли повисшие ссылки).

        q_ids = list(
            self._session.execute(
                select(Query.id).where(Query.user_id == str(user_id))
            ).scalars().all()
        )
        if not q_ids:
            return

        self._session.execute(delete(QueryResultItem).where(QueryResultItem.query_id.in_(q_ids)))
        self._session.execute(delete(Query).where(Query.id.in_(q_ids)))
        self._session.flush()

