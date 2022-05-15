from .calendar import fetch_calblocks, top_of_hour
from .config import config, get_tz, get_start_workday, get_end_workday, get_end_view
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
