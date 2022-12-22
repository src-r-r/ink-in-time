from sqlalchemy.engine import create_mock_engine
from iit.cal.source import RemoteCalendarSource
# from iit.config import config
import arrow

def test_calendar_compiler():
    TEST_URL = "http://localhost:5002/ics/maybe-their.ics/"
    source = RemoteCalendarSource(TEST_URL)
    assert len([e for e in source.get_events()])