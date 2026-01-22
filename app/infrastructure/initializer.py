# app/infrastructure/demo.py
from decimal import Decimal
from uuid import UUID

from database.database import Base, init_db, get_engine, get_session
from services.user_service import UserService
from services.transaction_service import TransactionService
from services.document_service import DocumentService
from services.search_service import SearchService
from services.index_service import IndexService
from services.auth_service import AuthService

from infrastructure.vector_index_model import VectorIndexModel
from infrastructure.dummy_embedding_model import DummyEmbeddingModel
from infrastructure.md5_hasher import Md5PasswordHasher
from models.user import UserRole
from database.config import DatabaseSettings



def init(settings: DatabaseSettings, drop_all: bool = True) -> None:
    init_db(settings)
    engine = get_engine()

    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with get_session() as session:
        # зависимости
        password_hasher = Md5PasswordHasher()
        embedder = DummyEmbeddingModel()
        vector_index = VectorIndexModel(session, model_name=embedder.name)

        # сервисы
        user_service = UserService(session, password_hasher)
        transaction_service = TransactionService(session)
        index_service = IndexService(session, vector_index, embedder)
        document_service = DocumentService(session, transaction_service, index_service)
        search_service = SearchService(session, transaction_service, index_service)
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

            print("== Загрузка пользовательских доков, должны сняться кредиты, и 'индексироваться' доки ==")
            d1 = document_service.add_document(UUID(user.id), "Cats", "Cats are wonderful animals")
            d2 = document_service.add_document(UUID(user.id), "Dogs", "Dogs are loyal friends")
            print(document_service.list_documents(UUID(user.id)))

            print("== Состояние пользователей ==")
            print(user)
            print("User " , user.login, "balance:", transaction_service.get_balance(UUID(user.id)))
            print(admin)
            print("User " , admin.login, "balance:", transaction_service.get_balance(UUID(admin.id)))

            print("== Поиск ==")
            results = search_service.search(UUID(user.id), "cats animals", top_k=5)

            print("== Результаты поиска (через dummy заглушку embedder) ==")
            print("Query ID:", results.query_id)
            for item in results.items:
                doc = document_service.get_document(UUID(user.id), item.document_id)
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
