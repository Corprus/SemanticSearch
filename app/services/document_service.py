# app/services/document_service.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.models.document import Document
from common.models.transaction import Transaction, TransactionType
from common.exceptions import DocumentNotFoundException, AccessDeniedException, UserNotExistsException
from common.models.user import User
from services.transaction_service import TransactionService
from services.index_service import IndexService

from infrastructure.worker_client import worker_app, TASK_EMBED_DOCUMENT_NAME
class DocumentService:

    def __init__(
        self,
        session: Session,
        transaction_service: TransactionService,
        index_service: IndexService,
        upload_cost: Decimal = Decimal("1.00"),
    ):
        self._session = session
        self._transaction_service = transaction_service
        self._index = index_service
        self._upload_cost = upload_cost

    def add_document(self, user_id: UUID, title: str, content: str) -> Document:
        """
        Добавить (загрузить) документ в систему
        Тут будет сразу и списываться кредит за загрузку
        """
        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        # списываем кредит
        # создаём документ
        doc = Document(
            owner_id=str(user_id),
            title=title,
            content=content,
        )
        self._session.add(doc)
        self._session.flush()


        transaction_id = self._transaction_service.withdraw_credit(user_id, self._upload_cost, reason=TransactionType.DOCUMENT_UPLOAD, reference_id=UUID(doc.id))

        # проставляем транзакции причину и ссылку на документ
        tx = self._session.get(Transaction, str(transaction_id))
        if tx is not None:
            tx.reason = TransactionType.DOCUMENT_UPLOAD.value
            tx.reference_id = doc.id
            self._session.add(tx)
            self._session.flush()

        # индексируем
        self._session.commit()
        worker_app.send_task(TASK_EMBED_DOCUMENT_NAME, args=[str(user_id), str(doc.id)])

        return doc

    def get_user_document(self, user_id: UUID, document_id: UUID) -> Document:
        """
        Получить документ пользователя из системы
        """
        doc = self._session.get(Document, str(document_id))
        if doc is None:
            raise DocumentNotFoundException()
        if doc.owner_id != str(user_id):
            raise AccessDeniedException()
        
        self._session.refresh(doc)  # <-- ВОТ ЭТО
        return doc

    def get_document(self, document_id: UUID) -> Document:
        """
        Получить документ из системы
        """
        doc = self._session.get(Document, str(document_id))
        if doc is None:
            raise DocumentNotFoundException()
        return doc


    def list_documents(self, user_id: UUID) -> list[Document]:
        """
        Получить документы пользователя
        """
        query = select(Document).where(Document.owner_id == str(user_id)).order_by(Document.created_at.desc())
        return list(self._session.execute(query).scalars().all())
        

    def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        """
        Удалить документ из системы
        """
        doc = self._session.get(Document, str(document_id))
        if doc is None:
            raise DocumentNotFoundException()
        if doc.owner_id != str(user_id):
            raise AccessDeniedException()

        self._session.delete(doc)
        self._session.flush()

        self._index.remove_document(user_id, document_id)
