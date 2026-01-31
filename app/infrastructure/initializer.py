# app/infrastructure/initializer.py
from decimal import Decimal
from uuid import UUID
import time

from common.database.database import Base, init_db, get_engine, get_session
from common.infrastructure.vector_index_model import VectorIndexModel
from common.database.config import DatabaseSettings

from services.user_service import UserService
from services.transaction_service import TransactionService
from services.document_service import DocumentService
from services.search_service import SearchService
from services.index_service import IndexService
from services.auth_service import AuthService


from common.models.user import UserRole
from common.models.query import QueryJobStatus
from common.models.document import DocumentIndexStatus

from infrastructure.md5_hasher import Md5PasswordHasher

def init(settings: DatabaseSettings, drop_all: bool = True) -> None:
    init_db(settings)
    engine = get_engine()

    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with get_session() as session:
        # зависимости
        password_hasher = Md5PasswordHasher()
        vector_index = VectorIndexModel(session)

        # сервисы
        user_service = UserService(session, password_hasher)
        transaction_service = TransactionService(session)
        index_service = IndexService(session, vector_index)
        document_service = DocumentService(session, transaction_service, index_service)
        search_service = SearchService(session, transaction_service)
        auth_service = AuthService(user_service, password_hasher)

        if drop_all:
            print("== DEMO START ==")
            # Создаём классы, показываем демку 
            print("== Создаем пользователей ==")
            user = user_service.create_user("demo", "demo123", role=UserRole.USER)
            admin = user_service.create_user("admin", "admin123", role=UserRole.ADMIN)

            print("== Даём кредиты пользователю ==")
            transaction_service.add_credit(UUID(user.id), Decimal("10.00"))

            print("== Состояние пользователей ==")
            print(user)
            print("User " , user.login, "balance:", transaction_service.get_balance(UUID(user.id)))
            print(admin)
            print("User " , admin.login, "balance:", transaction_service.get_balance(UUID(admin.id)))

            print("== Загрузка пользовательских доков, должны сняться кредиты, и индексироваться доки ==")
            d1 = document_service.add_document(UUID(user.id), "Cats", "Cats are wonderful animals")
            d2 = document_service.add_document(UUID(user.id), "Dogs", "Dogs are loyal friends")

            print(document_service.list_documents(UUID(user.id)))

            deadline = time.time() + 120.0
            while True:
                qr1 = document_service.get_user_document(UUID(user.id), document_id=UUID(d1.id))
                status1 = qr1.index_status
                qr2 = document_service.get_user_document(UUID(user.id), document_id=UUID(d2.id))
                status2 = qr2.index_status

                if status1 == DocumentIndexStatus.INDEXED.value and status2 == DocumentIndexStatus.INDEXED.value:                    
                    print(qr1)
                    print(qr2)
                    break

                if status1 == DocumentIndexStatus.FAILED.value or status2 == DocumentIndexStatus.FAILED.value:
                    raise RuntimeError("Index failed")

                if time.time() >= deadline:
                    raise TimeoutError("Indexing timeout")
                timetowait = 5
                print(f"Doc id {qr1.id} status {status1}, Doc id {qr2.id} status {status2}. Waiting to index for {timetowait} sec")
                time.sleep(timetowait)  # 5 сек

            print("== Состояние пользователей ==")
            print(user)
            print("User " , user.login, "balance:", transaction_service.get_balance(UUID(user.id)))
            print(admin)
            print("User " , admin.login, "balance:", transaction_service.get_balance(UUID(admin.id)))

            print("== Поиск ==")

            query_id = search_service.create_query_job(UUID(user.id), "cats animals", top_k=5)
            print("== Поиск поставлен в очередь ==")

            deadline = time.time() + 10.0  # 10 секунд на демо
            while True:
                query_results = search_service.get_query_results(UUID(user.id), query_id, limit=50, offset=0)
                status = query_results.query.query_status

                if status == QueryJobStatus.DONE.value:
                    print(f"Query {query_id} status {status} ")
                    results = query_results
                    break

                if status == QueryJobStatus.FAILED.value:
                    raise RuntimeError(f"Search failed for query_id={query_id}")

                if time.time() >= deadline:
                    raise TimeoutError(f"Search timeout for query_id={query_id}")

                timetowait = 5
                print(f"Query {query_id} status {status}, waiting for {timetowait} sec")
                time.sleep(timetowait)

            print("== Результаты поиска ==")
            print("Query ID:", results.query_id)
            for item in results.items:
                doc = document_service.get_user_document(UUID(user.id), item.document_id)
                print(f"rank={item.rank} score={item.score:.3f} doc='{doc.title}' id={item.document_id}")

            print("== История транзакций ==")
            for tx in transaction_service.get_transaction_history(UUID(user.id)):
                print(tx)

            print("== Состояние пользователей ==")
            print(user)
            print("User " , user.login, "balance:", transaction_service.get_balance(UUID(user.id)))
            print(admin)
            print("User " , admin.login, "balance:", transaction_service.get_balance(UUID(admin.id)))

            session.commit()
            print("== DEMO DONE ==")
