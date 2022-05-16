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
(block, start, end)
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
    conn = sqlite3.connect(config.database_path)
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


def dtint(dt: datetime, tzinfo=pytz.utc):
    return int(tzinfo.localize(dt).timestamp())


def intdt(t: int, tzinfo=pytz.utc):
    dt = datetime.fromtimestamp(t, tz=tzinfo)
    import ipdb

    ipdb.set_trace()
    return dt


A = arrow.get


def compile_choices(inittime=arrow.now(tz=str(config.my_timezone))):
    conn = get_db()
    curr = conn.cursor()
    curr.execute(CLEAR_CHOICES)
    conn.commit()
    curr = conn.cursor()
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
            curr.execute(INSERT_CHOICE, values)
        conn.commit()
    curr.close()


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
