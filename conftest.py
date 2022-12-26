import os
import pytest
from iit.cal.source.remote import RemoteCalendarSource
from iit.mock.cal.source import StaticMockCalendarSource
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.engine import create_engine

import arrow
import pytest

@pytest.fixture
def Session():
    from iit.models.block import Base, Session as BaseSession, engine
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def remote_compiled_calendar(Session):
    from iit.cal.block.compiler import PostgresBlockCompiler
    from iit.cal.compiler import PostgresCalendarCompiler

    lower = arrow.now()
    upper = arrow.now().shift(months=1)
    duratio = timedelta(minutes=60)
    block_compiler = PostgresBlockCompiler(
        lower,
        upper,
        duration,
        "60min",
    )
    source = RemoteCalendarSource("http://127.0.0.1:5002/test.ics")
    calendar_compiler = PostgresBlockCompiler(source)
    calendar_compiler.compile()
    return None


@pytest.fixture()
def app():
    from iit.iit_app import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


# @pytest.fixture
# def metadata():
#     engine = create_engine(os.getenv("DB_URL"))
#     Base.metadata.create_all(engine)
#     _session = Session()
#     yield Base.metadata
#     Base.metadata.drop_all(engine)
#     _session.rollback()
#     _session.close()
