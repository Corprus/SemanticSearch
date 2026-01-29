# app/infrastructure/worker_task.py
from uuid import UUID
from celery.utils.log import get_task_logger

from infrastructure.worker_app import worker_app
from database.database import get_session
from infrastructure.dummy_embedding_model import DummyEmbeddingModel
from infrastructure.vector_index_model import VectorIndexModel
from models.document import DocumentIndexStatus
logger = get_task_logger(__name__)

@worker_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def embed_document(self, user: str, document_id: str) -> None:
    from services.index_service import IndexService
    from services.transaction_service import TransactionService
    from services.document_service import DocumentService

    doc_id = UUID(document_id)
    user_id = UUID(user)

    logger.info(f"Embedding started: document_id={doc_id}")

    with get_session() as session:
        embedder = DummyEmbeddingModel()
        vector_index = VectorIndexModel(session, model_name=embedder.name)
        index_service = IndexService(session, vector_index, embedder)
        transaction_service = TransactionService(session)
        document_service = DocumentService(session, transaction_service, index_service)

        index_service.index_document(user_id=user_id, document_id=doc_id)
        document_service.set_index_status(doc_id, DocumentIndexStatus.INDEXED)
        session.commit()

    logger.info(f"Embedding finished: document_id={doc_id}")


DEFAULT_TOP_K = 10

@worker_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def process_search_query(self, query_id: str) -> None:
    from services.index_service import IndexService
    from services.transaction_service import TransactionService
    from services.search_service import SearchService

    q_id = UUID(query_id)
    logger.info(f"Search started: query_id={q_id}")

    with get_session() as session:
        embedder = DummyEmbeddingModel()
        vector_index = VectorIndexModel(session, model_name=embedder.name)

        transaction_service = TransactionService(session)
        index_service = IndexService(session, vector_index, embedder)
        search_service = SearchService(session, transaction_service, index_service)

        search_service.process_query_job(q_id)
        session.commit()

    logger.info(f"Search finished: query_id={q_id}")