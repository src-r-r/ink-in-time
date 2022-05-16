from .calendar import fetch_calblocks, top_of_hour
from .config import config, get_tz, get_start_workday, get_end_workday, get_end_view
from .tasks import compile_choices, get_db, fetch_choices
from datetime import datetime, timedelta
import pytz
import logging

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
    tz = get_tz()
    starttime = get_start_workday()
    endtime = get_end_workday()
    now = tz.fromutc(datetime.utcnow())
    env_view = get_end_view(now)
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