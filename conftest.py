import os
import pytest
from datetime import timedelta
from iit.config import DB_URL
from iit.core.workweek import get_workweek
from iit.cal.source.remote import RemoteCalendarSource
from iit.mock.cal.source import StaticMockCalendarSource
from iit.cal.block.compiler import PostgresIitBlockCompiler
from iit.cal.compiler import PostgresCalendarCompiler
from iit.models.block import Base, Session as BaseSession, engine

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
    Session,
    scoped_session,
)

import arrow
import pytest


@pytest.fixture
def test_config():
    return {
        "scheduling": {
            "appointments": {
                "Full Consultation": 60,
            },
        },
        "site": {"url_base": "http://127.0.0.1/schedule"},
        "scheduling": {
            "work_week": [
                ("mon-f", "8AM - 11 a, 1PM - 7:00PM"),
                ("sat", "10AM - 4PM"),
            ],
        },
    }


@pytest.fixture
def weekly_schedule(test_config):
    return get_workweek(test_config)


@pytest.fixture(scope="session")
def db_engine(request):
    """yields a SQLAlchemy engine which is suppressed after the test session"""
    # db_url = request.config.getoption("--dburl")
    engine_ = create_engine(DB_URL, echo=True)

    yield engine_

    engine_.dispose()


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """returns a SQLAlchemy scoped session factory"""
    return scoped_session(sessionmaker(bind=db_engine))


@pytest.fixture(scope="function")
def db_session(db_session_factory):
    """yields a SQLAlchemy connection which is rollbacked after the test"""
    session_ = db_session_factory()

    yield session_

    session_.rollback()
    session_.close()


@pytest.fixture
def remote_compiled_calendar(db_session, weekly_schedule):
    lower = arrow.now()
    upper = arrow.now().shift(months=1)
    duration = timedelta(minutes=60)
    block_compiler = PostgresIitBlockCompiler(
        db_session,
        weekly_schedule,
        lower,
        upper,
        duration,
        "Full Consultation",
    )
    block_compiler.compile()
    source = RemoteCalendarSource("http://127.0.0.1:5002/test.ics")
    calendar_compiler = PostgresCalendarCompiler(
        source,
    )
    calendar_compiler.compile()
    return None


@pytest.fixture()
def app(test_config):
    from iit.iit_app import create_app

    app = create_app(iit_config=test_config)
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
