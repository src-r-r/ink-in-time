from icalendar import Calendar, Event, vCalAddress, vText
from faker import Faker
import pytz
import arrow
import random
import logging
import logging.config
from .config import MOCK_ICS_DIR, config
log = logging.getLogger(__name__)

fake = Faker()

def mock_tzname():
    return random.choice([x for x in pytz.all_timezones_set])

def mock_tz():
    return pytz.timezone(mock_tzname)

def mock_calendar():
    cal = Calendar()
    return cal

def mock_organizer():
    organizer = vCalAddress("MAILTO:" + fake.ascii_safe_email())
    organizer.params["cn"] = fake.name()
    return organizer

def mock_event(after : arrow.Arrow, organizer : vCalAddress = None, end_shift_kw=None):
    end_shift_kw = end_shift_kw or dict(hours=+6)
    start_dt = fake.date_time_between(after.datetime, "+1d", tzinfo=after.tzinfo)
    start_arr = arrow.get(start_dt)
    end_arr = start_arr.shift(**end_shift_kw)
    end_dt = end_arr.datetime
    event = Event()
    event.add("summary", fake.sentence())
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    event.add("organizer", organizer or mock_organizer())

    log.debug("Event: %s", event)

    return (event, end_arr)

def mock_ics(start=arrow.utcnow(), end=arrow.utcnow().shift(weeks=2)):
    cal = mock_calendar()
    organizer = mock_organizer()
    # Start at midnight tomorrow (just to keep it easy)
    start = start\
        .shift(days=+1)\
        .replace(hour=0, minute=0, second=0)\
        .to(mock_tzname())
    # Fill the calendar with events for 2 weeks
    dt = start
    while dt < end:
        (event, dt) = mock_event(dt, organizer)
        cal.add_component(event)
    return cal

def do_generation(start=arrow.utcnow()):
    MOCK_ICS_DIR.mkdir(parents=True, exist_ok=True)
    ics_name = "-".join(fake.words(2)).lower()
    ics_path = MOCK_ICS_DIR / str(ics_name + ".ics")
    ics = mock_ics()
    ics_path.write_bytes(ics.to_ical())

if __name__ == '__main__':
    logging.config.dictConfig(config.LOGGING)
    do_generation()