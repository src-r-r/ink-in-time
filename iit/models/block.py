import os
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declared_attr, declarative_mixin, sessionmaker
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    UniqueConstraint,
    Boolean,
)
from environ import Env
from psycopg2.extras import Range
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import TSTZRANGE
# from sqlalchemy.orm import Mapped
# from sqlalchemy.orm import mapped_column

Base = declarative_base()

log = logging.getLogger(__name__)

@declarative_mixin
class Model:
    id = Column(Integer, primary_key=True)
    @declared_attr
    def __tablename__(self):
        return type(self).__name__.lower()

class Block(Model, Base):
    name = Column(String(512))
    during = Column(TSTZRANGE())
    is_unavailable = Column(Boolean, nullable=True)

    __table_args__ = (UniqueConstraint("name", "during"),)


env = Env()
Env.read_env(".env")

db_url = env.str("DB_URL")
engine = create_engine(db_url, echo=True)
Session = sessionmaker(bind=engine)