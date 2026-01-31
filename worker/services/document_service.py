# app/services/document_service.py
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from common.models.document import Document, DocumentIndexStatus
from common.exceptions import DocumentNotFoundException

class DocumentService:

    def __init__(
        self,
        session: Session
    ):
        self._session = session

    def set_index_status(
        self,
        document_id: UUID,
        status: DocumentIndexStatus,
        error: str | None = None,
    ) -> None:
        """
        Проставить статус документу
        """
        doc = self._session.get(Document, str(document_id))
        if doc is None:
            raise DocumentNotFoundException()

        doc.index_status = status.value
        doc.index_error = error

        if status == DocumentIndexStatus.INDEXED:
            doc.indexed_at = datetime.now(timezone.utc)
        else:
            doc.indexed_at = None

        self._session.add(doc)
        self._session.flush()
