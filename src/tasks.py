import sqlite3
from pathlib import Path
from .config import get_db_path, get_appts, get_tz
from .calendar import calblock_choices, fetch_calblocks
from datetime import timedelta, datetime
import logging
import pytz
log = logging.getLogger(__name__)

TABLENAME = "choices"

# start and end will be seconds since epoch, UTC
MIGRATIONS = [
    f"""CREATE TABLE IF NOT EXISTS {TABLENAME} (
        block TEXT,
        start INT,
        end INT
    )
    """,
]

CLEAR_CHOICES = f"""
DELETE FROM {TABLENAME};
"""

INSERT_CHOICE = f"""
INSERT INTO {TABLENAME}
block, start, end
VALUES
(?,     ?,     ?  )
"""

SELECT_BY_BLOCK = f"""
SELECT block, start, end FROM {TABLENAME}
WHERE block=?
"""

SELECT_BY_BLOCK_AND_DATE = f"""
SELECT block, start, end FROM {TABLENAME}
WHERE block=?
AND
    start >= ?
    AND
    end <= ?
"""

def get_db():
    conn = sqlite3.connect(get_db_path())
    curr = conn.cursor()
    for migration in MIGRATIONS:
        log.info("Executing migration: %s", migration)
        curr.execute(migration)
        conn.commit()
    curr.close()
    return conn

def setup():
    for migration in MIGRATIONS:
        with dbcurs() as curs:
            curr.execute(migration)
            curs.commit()


def dtint(dt : datetime):
    return int(pytz.utc.localize(dt).timestamp())

def intdt(t : int):
    return pytz.utc.localize(datetime.fromtimestamp(t))

def compile_choices(inittime=datetime.now(get_tz())):
    conn = get_db()
    curr = conn.cursor()
    curr.execute(CLEAR_CHOICES)
    conn.commit()
    curr = conn.cursor()
    for (key, appt) in get_appts().items():
        d = timedelta(minutes=appt["time"])
        log.debug("Insert %s blocks", key)
        for cb in fetch_calblocks(d, inittime):
            curr.execute(INSERT_CHOICE, (key, dtint(cb.start), dtint(cb.end)))
        conn.commit()
    curr.close()

def normalize_record(record):
    # Convert the int value to a utc datetime
    (block, start, end) = record
    start = intdt(start)
    end = intdt(end)
    return (block, start, end)

def fetch_choices(block, year=None, month=None, day=None, tzinfo=None):
    
    # If a year is't given return the base query
    if not year:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(SELECT_BY_BLOCK, (block, ))
        record = cursor.fetchone()
        while record:
            yield normalize_record(record)
            record = cursor.fetchone()
        conn.close()
        return
    
    # If any other date params are given, construct
    # the date restriction
    start = datetime(year=year, month=month or 1, day=day or 1, tzinfo=tzinfo)
    if year and month and day:
        end = start + timedelta(day=1)
    elif year and month:
        if start.month == 12:
            end = datetime(year=start.year+1, month=1, day=day, tzinfo=tzinfo)
        else:
            end = datetime(year=start.year, month=start.month+1, day=start.day, tzinfo=tzinfo)
    else:
        end = datetime(year=start.year+1, month=start.month, day=start.day, tzinfo=tzinfo)
    
    
    # now convert to utc to match database
    start_utc = dtint(start)
    end_utc = dtint(end)
    # 1640995200 -> 1672531200
    log.debug("Query between %s -> %s", start_utc, end_utc)

    # filter for the events that match
    conn = get_db()
    curs = conn.cursor()
    curs.execute(SELECT_BY_BLOCK_AND_DATE, (block, start_utc, end_utc))
    record = curs.fetchone()
    while record:
        yield normalize_record(record)
        record = curs.fetchone()
    conn.close()
    return
