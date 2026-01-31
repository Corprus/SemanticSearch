# app/infrastructure/worker_task.py
import os
from uuid import UUID
from celery.utils.log import get_task_logger

from common.database.database import get_session
from common.infrastructure.vector_index_model import VectorIndexModel
from common.models.document import DocumentIndexStatus

from worker.worker_app import worker_app
from worker.infrastructure.sentence_transformer_embedding_model import SentenceTransformerEmbeddingModel

logger = get_task_logger(__name__)
TASK_EMBED_DOCUMENT_NAME = os.getenv("TASK_EMBED_DOCUMENT_NAME", "embed_document")
TASK_PROCESS_SEARCH_QUERY_NAME = os.getenv("TASK_PROCESS_SEARCH_QUERY_NAME", "process_search_query")

@worker_app.task(bind=True, name=TASK_EMBED_DOCUMENT_NAME, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def embed_document(self, user: str, document_id: str) -> None:
    from worker.services.index_service import IndexService
    from worker.services.document_service import DocumentService

    doc_id = UUID(document_id)
    user_id = UUID(user)

    logger.info(f"Embedding started: document_id={doc_id}")

    with get_session() as session:
        #embedder = DummyEmbeddingModel()
        embedder = SentenceTransformerEmbeddingModel()
        vector_index = VectorIndexModel(session)
        index_service = IndexService(session, vector_index, embedder)
        document_service = DocumentService(session)

        vector = index_service.index_document(user_id=user_id, document_id=doc_id)
        
        document_service.set_index_status(doc_id, DocumentIndexStatus.INDEXED)
        session.commit()

    logger.info(f"Embedding finished: document_id={doc_id}")


DEFAULT_TOP_K = 10

@worker_app.task(bind=True, name=TASK_PROCESS_SEARCH_QUERY_NAME, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def process_search_query(self, query_id: str) -> None:
    from worker.services.index_service import IndexService
    from worker.services.search_service import SearchService

    q_id = UUID(query_id)
    logger.info(f"Search started: query_id={q_id}")

    with get_session() as session:
        embedder = SentenceTransformerEmbeddingModel()
        vector_index = VectorIndexModel(session)

        index_service = IndexService(session, vector_index, embedder)
        search_service = SearchService(session, index_service)

        search_service.process_query_job(q_id)
        session.commit()

    logger.info(f"Search finished: query_id={q_id}")