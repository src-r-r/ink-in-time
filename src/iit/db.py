import sqlite3
from calendar import month_name
from pathlib import Path
from .config import config
from .calendar import calblock_choices, fetch_calblocks
from .timespan import TimeSpan
from datetime import timedelta, datetime
import arrow
import logging
import pytz

log = logging.getLogger(__name__)

CHOICES = "choices"
STATE = "state"
CHOICES_PRIMARY = f"{CHOICES}_primary"
CHOICES_SECONDARY = f"{CHOICES}_secondary"
STATE_FREE = "free"
STATE_LOCKED = "locked"
# start and end will be seconds since epoch, UTC
MIGRATIONS = [
    # compiling the calendars take a while, so we need
    # to come up with a semaphore-like infrastructure.
    f"""CREATE TABLE IF NOT EXISTS {CHOICES_PRIMARY} (
        block TEXT,
        start INT,
        end INT
    )""",
    f"""CREATE TABLE IF NOT EXISTS {CHOICES_SECONDARY} (        
        block TEXT,
        start INT,
        end INT
    )""",
    f"""CREATE TABLE IF NOT EXISTS {STATE} (
        tbl TEXT,
        state TEXT,
        lastrun INT
    )""",
]

LOCK_PRIMARY_TABLE = f"""
    UPDATE {STATE}
    SET state='{STATE_LOCKED}'
    WHERE tbl='primary'
"""

UNLOCK_PRIMARY_TABLE = f"""
    UPDATE {STATE}
    SET state='{STATE_FREE}'
    WHERE tbl='primary'
"""

LOCK_SECONDARY_TABLE = f"""
    UPDATE {STATE}
    SET state='{STATE_LOCKED}'
    WHERE tbl='secondary'
"""

UNLOCK_SECONDARY_TABLE = f"""
    UPDATE {STATE}
    SET state='{STATE_FREE}'
    WHERE tbl='secondary'
"""

IS_PRIMARY_IN_STATE = f"""
SELECT COUNT(*) FROM {STATE}
WHERE tbl='primary';
"""

SET_PRIMARY_INITIAL_FREE = f"""
INSERT INTO {STATE}
(tbl, state)
VALUES
('primary', 'free')
"""

SET_SECONDARY_INITIAL_FREE = f"""
INSERT INTO {STATE}
(tbl, state)
VALUES
('secondary', 'free')
"""

IS_SECONDARY_IN_STATE = f"""
SELECT COUNT(*) FROM {STATE}
WHERE tbl='secondary';
"""

IS_PRIMARY_LOCKED = f"""
    SELECT COUNT(*)
    FROM {STATE}
    WHERE
        tbl='primary' AND
        state='{STATE_LOCKED}'
"""

IS_PRIMARY_FREE = f"""
    SELECT COUNT(*)
    FROM {STATE}
    WHERE
        tbl='primary' AND
        state='{STATE_FREE}'
"""

DOES_PRIMARY_OR_SECONDARY_EXIST = f"""
    SELECT COUNT(*)
    FROM {CHOICES_PRIMARY}, {CHOICES_SECONDARY}
"""

UPDATE_PRIMARY_LAST_RUN = f"""
    UPDATE {STATE}
    SET lastrun = ?
    WHERE tbl='primary'
"""

UPDATE_SECONDARY_LAST_RUN = f"""
    UPDATE {STATE}
    SET lastrun = ?
    WHERE tbl='primary'
"""

GET_LAST_RUN_PRIMARY = f"""
    SELECT lastrun
    FROM {STATE}
    WHERE
        tbl='primary'
"""

GET_LAST_RUN_SECONDARY = f"""
    SELECT lastrun
    FROM {STATE}
    WHERE
        tbl='secondary'
"""

CLEAR_PRIMARY = f"""
DELETE FROM {CHOICES_PRIMARY};
"""

CLEAR_SECONDARY = f"""
DELETE FROM {CHOICES_SECONDARY};
"""

INSERT_CHOICE_PRIMARY = f"""
INSERT INTO {CHOICES_PRIMARY}
(block, start, end)
VALUES
(?,     ?,     ?  )
"""

SELECT_BY_BLOCK_PRIMARY = f"""
SELECT block, start, end FROM {CHOICES_PRIMARY}
WHERE block=?
"""

SELECT_BY_BLOCK_SECONDARY = f"""
SELECT block, start, end FROM {CHOICES_SECONDARY}
WHERE block=?
"""

SELECT_BY_BLOCK_AND_DATE_PRIMARY = f"""
SELECT block, start, end FROM {CHOICES_PRIMARY}
WHERE block=?
AND
    start >= ?
    AND
    end <= ?
"""

SELECT_BY_BLOCK_AND_DATE_SECONDARY = f"""
SELECT block, start, end FROM {CHOICES_SECONDARY}
WHERE block=?
AND
    start >= ?
    AND
    end <= ?
"""

DUPLICATE_PRIMARY_TO_SECONDARY = f"""
INSERT INTO {CHOICES_SECONDARY}
SELECT * FROM {CHOICES_PRIMARY}
"""
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
