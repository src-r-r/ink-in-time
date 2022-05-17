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

def ensure_state_tables(conn):
    curs = conn.cursor()
    curs.execute(IS_PRIMARY_IN_STATE)
    if not int(curs.fetchone()[0]):
        curs.execute(SET_PRIMARY_INITIAL_FREE)
        conn.commit()
    curs.execute(IS_SECONDARY_IN_STATE)
    if not int(curs.fetchone()[0]):
        curs.execute(SET_SECONDARY_INITIAL_FREE)
        conn.commit()
    curs.close()

def get_db():
    conn = sqlite3.connect(config.database_path)
    curr = conn.cursor()
    for migration in MIGRATIONS:
        log.info("Executing migration: %s", migration)
        curr.execute(migration)
        conn.commit()
    curr.close()
    ensure_state_tables(conn)
    return conn


def setup():
    for migration in MIGRATIONS:
        with dbcurs() as curs:
            curr.execute(migration)
            curs.commit()


def dtint(dt: datetime, tzinfo=pytz.utc):
    return int(tzinfo.localize(dt).timestamp())


def intdt(t: int, tzinfo=pytz.utc):
    dt = datetime.fromtimestamp(t, tz=tzinfo)
    import ipdb

    ipdb.set_trace()
    return dt


A = arrow.get


def lock_primary_table():
    conn = get_db()
    curs = conn.cursor()
    log.info("LOCKING PRIMARY TABLE")
    log.debug(LOCK_PRIMARY_TABLE)
    curs.execute(LOCK_PRIMARY_TABLE)
    conn.commit()
    conn.close()

def unlock_primary_table():
    conn = get_db()
    curs = conn.cursor()
    log.debug(UNLOCK_PRIMARY_TABLE)
    curs.execute(UNLOCK_PRIMARY_TABLE)
    log.info("PRIMARY TABLE UNLOCKED")
    conn.commit()
    conn.close()

def set_lastrun_primary(when=arrow.utcnow()):
    conn = get_db()
    curs = conn.cursor()
    ts = int(when.timestamp())
    curs.execute(UPDATE_PRIMARY_LAST_RUN, (ts,))
    conn.commit()
    conn.close()

def get_lastrun_primary() -> arrow.Arrow:
    """ Get the last time the compilation was run (as UTC arrow) """
    conn = get_db()
    curs = conn.cursor()
    log.debug(GET_LAST_RUN_PRIMARY)
    curs.execute(GET_LAST_RUN_PRIMARY)
    result = curs.fetchone()
    curs.close()
    timestamp : int = result[0]
    if not timestamp:
        return None
    # already set to utc! :-)
    return arrow.get(int(timestamp))

def _bool_query(QUERY, TRUE_RES=1):
    conn = get_db()
    curs = conn.cursor()
    log.debug(QUERY)
    curs.execute(QUERY)
    result = curs.fetchone()
    conn.close()
    return int(result[0]) == TRUE_RES

def is_primary_locked():
    return _bool_query(IS_PRIMARY_LOCKED)

def is_primary_free():
    return _bool_query(IS_PRIMARY_FREE)

def duplicate_primary_to_secondary():
    conn = get_db()
    curs = conn.cursor()
    curs.execute(LOCK_SECONDARY_TABLE)
    curs.execute(CLEAR_SECONDARY)
    curs.execute(DUPLICATE_PRIMARY_TO_SECONDARY)
    curs.execute(UNLOCK_SECONDARY_TABLE)
    conn.commit()
    conn.close()


def compile_choices(inittime=arrow.now(tz=str(config.my_timezone))):
    # Check if there's already a lock. We typically shouldn't have this
    # happen, but it may result if the user has A LOT of calendar data
    # and the interval between fetches is too short.
    # Another instance is if there's an SQL error.
    if is_primary_locked():
        log.warning("Primary table is locked")
        return
    # First lock the primary table
    lock_primary_table()
    
    # Get a connection for this session
    conn = get_db()

    # clear the primary table
    curr = conn.cursor()
    curr.execute(CLEAR_PRIMARY)
    conn.commit()
    curr = conn.cursor()

    # Insert into the primary table
    for (key, appt) in config.appointments.items():
        d = appt.time
        log.debug("Insert blocks : %s", key)
        for cb in fetch_calblocks(d, inittime):
            start_utc = A(cb.start).to("UTC")
            end_utc = A(cb.end).to("UTC")
            if start_utc.tzinfo != cb.start.tzinfo:
                log.debug("  (converted start %s -> %s)", cb.end.tzinfo, end_utc.tzinfo)
            if end_utc.tzinfo != cb.end.tzinfo:
                log.debug("  (converted end %s -> %s)", cb.end.tzinfo, end_utc.tzinfo)
            startstamp = int(start_utc.timestamp())
            endstamp = int(end_utc.timestamp())
            values = (key, startstamp, endstamp)
            log.debug("  -> %s", values)
            curr.execute(INSERT_CHOICE_PRIMARY, values)
        conn.commit()
    curr.close()

    set_lastrun_primary()
    
    # Unlock the primary table
    unlock_primary_table()

    # duplicate the primary table to the secondary table.
    log.debug("Duplicating primary table...")
    duplicate_primary_to_secondary()
    log.debug("Done!")


def normalize_record(record):
    # Convert the int value to a utc datetime
    (block, start, end) = record
    start = arrow.get(start, tzinfo=pytz.utc)
    end = arrow.get(end, tzinfo=pytz.utc)
    return (block, start, end)


def localize_normalize_record(record, tzinfo):
    # Convert the int value to a localized datetime
    (block, start, end) = normalize_record(record)
    start = start.to(tzinfo)
    end = end.to(tzinfo)
    return (block, start, end)


def fetch_choices(block, year=None, month=1, day=1, tzinfo=None):

    SELECT_BY_BLOCK = SELECT_BY_BLOCK_PRIMARY
    SELECT_BY_BLOCK_AND_DATE = SELECT_BY_BLOCK_AND_DATE_PRIMARY
    if is_primary_locked():
        SELECT_BY_BLOCK = SELECT_BY_BLOCK_SECONDARY
        SELECT_BY_BLOCK_AND_DATE = SELECT_BY_BLOCK_AND_DATE_SECONDARY

    # If a year is't given return the base query
    if not year:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(SELECT_BY_BLOCK, (block,))
        record = cursor.fetchone()
        while record:
            yield localize_normalize_record(record, tzinfo)
            record = cursor.fetchone()
        conn.close()
        return

    # If any other date params are given, construct
    # the date restriction
    A = arrow.get
    start = A(year=year, month=month, day=day, tzinfo=tzinfo)
    if day:
        end = start.shift(days=+1)
    elif month:
        end = start.shift(months=+1)
    elif year:
        end = start.shift(years=+1)

    # now convert to utc to match database
    start_utc = start.to("UTC")
    end_utc = end.to("UTC")
    start_ts = int(start_utc.timestamp())
    end_ts = int(end_utc.timestamp())
    # 1640995200 -> 1672531200
    log.debug("Query between %s (%s) -> %s (%s)", start_ts, start_utc, end_ts, end_utc)

    # filter for the events that match
    conn = get_db()
    curs = conn.cursor()
    curs.execute(SELECT_BY_BLOCK_AND_DATE, (block, start_ts, end_ts))
    record = curs.fetchone()
    while record:
        log.debug(record)
        yield localize_normalize_record(record, tzinfo)
        record = curs.fetchone()
    conn.close()
    return


def fetch_more_human_choices(block=None, year=None, month=None, day=None, tzinfo=None):

    if not block:
        for (key, value) in get_appts().items():
            yield {
                "selection": "block",
                "block": None,
                "value": key,
                "label": value["label"] + " (" + value["duration"] + " min.)",
            }
        return

    log.info("Fetching choices with tz=%s", tzinfo)
    for (block, start, end) in fetch_choices(block, year, month, day, tzinfo):
        if year and month and day:
            value = TimeSpan(start, end).to_json()
            log.debug(value)
            yield {
                "selection": "time",
                "block": block,
                "value": value,
            }
        elif year and month:
            yield {
                "selection": "day",
                "block": block,
                "value": start.day,
                "label": start.day,
            }
        elif year:
            yield {
                "selection": "month",
                "block": block,
                "value": start.month,
                "label": list(month_name)[start.month],
            }
        else:
            yield {
                "selection": "year",
                "block": block,
                "value": start.year,
                "label": start.year,
            }