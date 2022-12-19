from sqlalchemy.orm import declared_attr
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import declarative_base

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

Base = declarative_base()

log = logging.getLogger(__name__)

class Model(Base):
    @declared_attr
    def __tablename__(self):
        return type(self).__name__.lower()

class Block(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(512))
    during: Mapped[Range[datetime]] = mapped_column(TSRANGE)
    is_unavailable = Column(Boolean, blank=True, nullable=True)

    __table_args__ = (UniqueConstraint("name", "during"),)
