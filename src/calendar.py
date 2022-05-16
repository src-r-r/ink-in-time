import typing as T
from .config import config, get_tz
import vobject
import requests
import logging
import pytz
import humanize as hu
import re
from cachetools import cached, LRUCache, TTLCache
from collections import namedtuple
from datetime import timedelta, datetime, time, date

log = logging.getLogger(__name__)

TimeBlock = namedtuple("TimeBlock", ["begin", "end"])


def mkdt(x):
    if isinstance(x, date) and not isinstance(x, datetime):
        return datetime(x.year, x.month, x.day, 0, 0, 0)
    return x


class Event:
    def __init__(self, calendar: "Calendar", start, end=None, sequence_event=None):
        if not end or sequence_event:
            raise RuntimeError("`end` or `sequence_event` required")
        self.calendar = calendar
        self._start = start
        self._end = end
        self.sequence_event = sequence_event

    @property
    def end(self):
        tz = self.calendar.timezone
        if self._end:
            e = self._end
        else:
            e = self.calendar.sequence_end(self.sequence_event)
        e = mkdt(e)
        if e.tzinfo:
            return e
        return tz.localize(e)

    @property
    def start(self):
        tz = self.calendar.timezone
        s = mkdt(self._start)
        if s.tzinfo:
            return s
        return tz.localize(s)

    @property
    def next(self):
        k = self.calendar._next_key(self.start)
        if not k:
            return None
        return self.calendar.events[k]

    def does_conflict(self, ambi_dt_start, ambi_dt_end):
        a1 = awareness(ambi_dt_start)
        a2 = awareness(ambi_dt_end)
        e1 = mkdt(self.start)
        e2 = mkdt(self.end)
        assert e1.tzinfo
        assert e2.tzinfo
        assert a1.tzinfo
        assert a2.tzinfo
        return (a1 < e1 and a2 > e2) or (a1 > e1 and a2 < e2) or (a1 < e2 and a2 > e2)


class Calendar:
    def __init__(self, timezone: pytz.timezone):
        self.timezone = timezone
        self.events = dict()
        self._sequences = dict()

    def sequence_end(self, event):
        return self._sequences[event["sequence"]]

    @property
    def start_date(self):
        return min(list(self.events.keys()))

    @property
    def end_date(self):
        return max(list(self.events.keys()))

    def _next_key(self, key):
        keys = list(self.events.keys())
        if key not in keys:
            return None
        next_i = keys.index(key) + 1
        if next_i >= len(keys):
            return None
        return keys[next_i]

    def add_event(self, vevent):
        start = vevent["dtstart"][0].value
        end = None
        sequence_event = None
        # If the event has an end date, set it.
        if "dtend" in vevent:
            end = vevent["dtend"][0].value
        # Otherwise, refer to the sequence
        elif "sequence":
            seq = vevent["sequence"][0].value
            if seq in self._sequences:
                sequence_event = self._sequences[seq]
        # If the squence has not been added, add it.
        if "sequence" in vevent:
            seq = vevent["sequence"][0].value
            if seq not in self._sequences:
                self._sequences[seq] = vevent
        # Assign the event to the start time.
        if start not in self.events:
            self.events[start] = []
        self.events[start].append(Event(self, start, end, sequence_event))

    def iter_all_events(self) -> T.Iterable[Event]:

        events = sorted(self.events.items(), key=lambda x: awareness(mkdt(x[0])))
        for e in events:
            yield e[1]

    def does_conflict(self, ambi_dt_start, ambi_dt_end):
        for eventset in self.iter_all_events():
            for event in eventset:
                if event.does_conflict(ambi_dt_start, ambi_dt_end):
                    return True
        return False


CalCol = T.Dict[T.AnyStr, T.Iterable[Calendar]]


class CalendarCollection:
    def __init__(self):
        self.cals: CalCol = {
            "free": [],
            "blocked": [],
        }

    def add_calendar(self, caltype, calendar):
        self.cals[caltype].append(calendar)

    def does_conflict(self, ambi_dt_start, ambi_dt_end):
        aware_dt_start = awareness(ambi_dt_start)
        aware_dt_end = awareness(ambi_dt_end)
        for cal in self.cals["blocked"]:
            if cal.does_conflict(aware_dt_start, aware_dt_end):
                return True
        return False


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def fetch_vobject(url) -> vobject.iCalendar:
    log.debug("Fetching %s", url)
    chunk = bytes()
    resp = requests.get(url)
    for event in vobject.readComponents(resp.text):
        yield event


def event_to_timeblock(event):
    if "dtend" not in event:
        log.warning("Event missing dtend: %s", event)
        return None
    return TimeBlock(begin=event["dtstart"][0].value, end=event["dtend"][0].value)


def get_events_from_vcal(vcal):
    for e in vcal.contents["vevent"]:
        yield e.contents


def get_tz_from_vcal(vcal) -> pytz.timezone:
    tz: T.AnyStr = vcal.contents["x-wr-timezone"][0].value
    return pytz.timezone(tz)


def construct_collection():
    calendars = config["calendars"]
    free = config["calendars"].get("free")
    blocked = config["calendars"].get("blocked")
    collection = CalendarCollection()
    for caltype in ("free", "blocked"):
        for cal in config["calendars"].get(caltype, []) or []:
            for vcal in fetch_vobject(cal):
                tz = get_tz_from_vcal(vcal)
                calendar = Calendar(tz)
                for event in get_events_from_vcal(vcal):
                    ev = event_to_timeblock(event)
                    if not ev:
                        continue
                    calendar.add_event(event)
                collection.add_calendar(caltype, calendar)
    return collection


def top_of_hour(when: datetime):
    n = when + timedelta(hours=1)
    return datetime(year=n.year, month=n.month, day=n.day, hour=n.hour)


def awareness(unaware: T.Union[datetime, time]) -> T.Union[datetime, time]:
    if unaware.tzinfo:
        return unaware
    return get_tz().localize(unaware)


def does_conflict(
    calcol: CalendarCollection, ambi_dt_start: datetime, ambi_dt_end: datetime
):
    aware_dt_start, aware_dt_end = (awareness(ambi_dt_start), awareness(ambi_dt_end))
    end_workday = time(**config["workday"]["end"])
    start_workday = time(**config["workday"]["end"])
    if ambi_dt_end.time() > end_workday:
        return True
    if ambi_dt_start.time() < start_workday:
        return True
    if calcol.does_conflict(aware_dt_start, aware_dt_end):
        return True
    return False


class TimeSpan:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    @property
    def duration(self):
        return self.end - self.start

    def to_json(self):
        return {
            "start": {
                "hour": self.start.hour,
                "minute": self.start.minute,
            },
            "end": {
                "hour": self.end.hour,
                "minute": self.minute.minute,
            },
            "duration_in_secs": self.duration.total_seconds(),
        }

    def __str__(self):
        s = self.start.strftime("%Y/%m/%d %H:%M")
        e = self.end.strftime("%Y/%m/%d %H:%M")
        d = hu.precisedelta(self.duration)
        return f"{s} -> {e} ({d})"

    def __repr__(self):
        return f"<TimeSpan (start={self.start}, end={self.end}, [duration={self.duration}])>"


def fetch_calblocks(
    duration: timedelta, inittime=datetime.now(get_tz())
) -> T.Iterable[TimeSpan]:
    inittime = awareness(inittime)
    grace = timedelta(**config["grace_period"])
    starttime = top_of_hour(inittime) + grace
    a1 = starttime
    collection = construct_collection()
    endspan = timedelta(**config["time_span"])
    endsequence = starttime + endspan
    # Now go through each of the `duration` blocks starting at inittime
    while a1 + duration < endsequence:
        a2 = a1 + duration
        log.debug("Checking for time %s -> %s (duration=%s)", a1, a2, duration)
        if not does_conflict(collection, a1, a2):
            yield TimeSpan(a1, a2)
        a1 = a2


@cached(LRUCache(1024))
def calblock_choices(
    duration: timedelta,
    year=None,
    month=None,
    day=None,
    inittime=datetime.now(get_tz()),
) -> T.Iterable[TimeSpan]:
    """Automagically returns the next choice in the chain given the input.

    TODO: Somhow this seems wrong; might need improvment

    Args:
        duration (timedelta): The duration of the appointment
        year (int, optional): Chosen year. Defaults to None.
        month (int, optional): Chosen month. Defaults to None.
        day (int, optional): Chosen day. Defaults to None.
        inittime (tz-aware datetime, optional): Initial time. Defaults to datetime.now(get_tz()).

    Returns:
        T.Iterable[T.Any]: depending...
            - list of years if nothing is selected
            - list of months if year is selected
            - list of days if month is selected
            - list of timespans (as json) if day is selected

    Yields:
        Iterator[T.Iterable[TimeSpan]]: _description_
    """
    for ts in fetch_calblocks(duration, inittime):
        ts: TimeSpan
        if year and ts.start.year == year:
            yield ts.start.month
        elif month and ts.start.month == month:
            yield ts.start.day
        elif day and ts.start.day == day:
            yield ts
        elif not year:
            yield ts.to_json()
