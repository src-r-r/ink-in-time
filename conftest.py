import os
import pytest
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.engine import create_engine

from iit.models.block import Base, Session as BaseSession, engine

@pytest.fixture
def Session():
    Base.metadata.create_all(engine)
    yield BaseSession
    Base.metadata.drop_all(engine)
    with BaseSession() as _session:
        _session.rollback()
        _session.close()

# @pytest.fixture
# def metadata():
#     engine = create_engine(os.getenv("DB_URL"))
#     Base.metadata.create_all(engine)
#     _session = Session()
#     yield Base.metadata
#     Base.metadata.drop_all(engine)
#     _session.rollback()
#     _session.close()