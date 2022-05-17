from datetime import datetime, timedelta, time
import pytest
import pytz
import logging
from .calendar import fetch_calblocks, top_of_hour
from .config import config
from .db import (
    compile_choices,
    get_db,
    fetch_choices,
    is_primary_locked,
    is_primary_free,
    get_lastrun_primary,
)
from .iit_app import create_app

log = logging.getLogger(__name__)


def test_top_of_hour():

    tm = datetime(2018, 1, 12, 8, 45, 15)
    expected = datetime(2018, 1, 12, 9, 0)
    toh = top_of_hour(tm)
    assert toh == expected

    # The next day!
    tm = datetime(2018, 1, 12, 23, 57, 00)
    expected = datetime(2018, 1, 13, 0, 0)
    toh = top_of_hour(tm)
    assert toh == expected


def test_fetch_calendars():
    tz = config.my_timezone
    starttime = config.start_workday
    endtime = config.end_workday
    now = tz.fromutc(datetime.utcnow())
    env_view = config.get_end_view_dt(now)
    duration = timedelta(minutes=90)
    for c in fetch_calblocks(duration):
        assert c.duration == duration
        assert c.start.time() > starttime
        assert c.end.time() < endtime


def test_compile_choices():
    compile_choices()
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM choices;")
    assert cur.fetchone()[0] > 0


def test_fetch_choices():
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    log.info("Fetching 60 minute blocks:")
    result = list(fetch_choices("60min"))
    a = len(result)
    assert a > 0

    log.info("Fetching 60 minute blocks in %d", year)
    result = list(fetch_choices("60min", year))
    b = len(result)
    assert 0 < a >= b

    log.info("Fetching 60 minute blocks in %d/%d", year, month)
    result = list(fetch_choices("60min", year, month))
    c = len(result)
    assert 0 < a >= b >= c

    log.info("Fetching 60 minute blocks in %d/%d/%d", year, month, day)
    result = list(fetch_choices("60min", year, month, day))
    d = len(result)
    assert 0 < a >= b >= c > d


@pytest.fixture
def app():
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


def test_views(client):
    now = datetime.now()
    resp = client.get("/")
    assert resp.status_code == 200
    resp = client.get(f"/30min/{now.year}/")
    assert resp.status_code == 200
    resp = client.get(f"/30min/{now.year}/{now.month}/")
    assert resp.status_code == 200
    resp = client.get(f"/30min/{now.year}/{now.month}/{now.day}/")
    assert resp.status_code == 200


from . import util
import arrow


def test_utils():
    naiive_dt = datetime.now()
    dt = arrow.utcnow()

    spans = (time(7, 0), time(20, 0), time(8, 0), time(13, 0))

    # This should raise an error since no ref_dt is given
    with pytest.raises(ValueError):
        util.arrows_conflict(*spans)
    # This should raise an error since ref_dt is naiive
    with pytest.raises(ValueError):
        util.arrows_conflict(*spans, ref_dt=naiive_dt)

    # raw times, with a conflict
    assert util.arrows_conflict(*spans, ref_dt=dt) == True

    # raw times, without a conflict
    spans = (time(7, 00), time(10, 00), time(12, 00), time(19, 0))
    assert util.arrows_conflict(*spans, ref_dt=dt) == False

    # test datetimes
    spans = (
        datetime(2022, 4, 1, 7, 0),
        time(8, 0),
        time(10, 0),
        time(13, 00),
    )
    with pytest.raises(ValueError):
        assert util.arrows_conflict(*spans) == True

    spans = (
        datetime(2022, 4, 1, 7, 0, 0, tzinfo=pytz.utc),
        time(8, 0),
        time(10, 0),
        time(13, 00),
    )
    assert util.arrows_conflict(*spans) == False

    spans = (
        datetime(2022, 4, 1, 7, 0, 0, tzinfo=pytz.utc),
        time(8, 0),
        time(10, 0),
        time(13, 00),
    )
    assert util.arrows_conflict(*spans) == False


def test_get_choices():

    now = arrow.utcnow()
    tzla = pytz.timezone("America/Los_Angeles")
    tzny = pytz.timezone("America/New_York")

    la_times = list(fetch_choices("30min", now.year, now.month, now.day, tzla))
    ny_times = list(fetch_choices("30min", now.year, now.month, now.day, tzny))

    # The times should be 3 hours apart
    for (i, la_time) in enumerate(la_times):
        assert ny_times[i] - la_types[i] == 3


import asyncio
import time
from multiprocessing import Process

async def start_background():
    compile_choices()


def test_primary_lock():
    """Test that databae semaphore locks

    IMPORTANT NOTE: make sure this database construction takes a while!
    """

    assert is_primary_free() == True
    assert is_primary_locked() == False
    assert get_lastrun_primary() is None

    proc = Process(target=compile_choices)
    proc.start()
    time.sleep(0.6)  # wait for a bit.

    assert is_primary_free() == False
    assert is_primary_locked() == True
    
    # wait for a bit more for the process to complete
    proc.join()
    assert is_primary_free() == True
    assert is_primary_locked() == False

    assert get_lastrun_primary() is not None
    
    # Just make sure it's recent and not wildly out of date
    assert get_lastrun_primary() > arrow.utcnow().shift(hours=-1)
    assert get_lastrun_primary() < arrow.utcnow().shift(hours=+1)

    # Also make sure the secondary table has been copied.
    db = get_db()
    curs = db.cursor()
    curs.execute("SELECT COUNT(*) FROM choices_secondary")
    secondary_count = curs.fetchone()[0]
    curs.execute("SELECT COUNT(*) FROM choices_primary")
    primary_count = curs.fetchone()[0]
    curs.close()
    assert secondary_count == primary_count