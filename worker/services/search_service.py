# app/services/search_service.py
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from common.models.query import Query, QueryJobStatus
from common.models.query_result_item import QueryResultItem
from common.models.document import Document

from worker.services.index_service import IndexService

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
        index_service: IndexService
    ):
        self._session = session
        self._index_service = index_service

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
            
            # 6) пишем QueryResultItem в БД (для истории)
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