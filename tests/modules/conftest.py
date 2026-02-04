import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB


# --- SQLite compatibility for PostgreSQL-specific column types ---
# Some of our SQLAlchemy models use PostgreSQL JSONB. For unit tests we use
# SQLite in-memory DB, so we provide a simple compilation rule.
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):  # noqa: D401
    return "JSON"


@pytest.fixture()
def engine():
    # in-memory DB is plenty for unit tests; keeps tests fast and isolated
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    # Importing models registers tables in metadata
    from common.database.database import Base
    import common.models.user  # noqa: F401
    import common.models.account  # noqa: F401
    import common.models.transaction  # noqa: F401
    import common.models.document  # noqa: F401
    import common.models.query  # noqa: F401
    import common.models.query_result_item  # noqa: F401
    import common.models.vector_index_entry  # noqa: F401

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as s:
        yield s
