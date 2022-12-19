import typing as T
import vobject
import requests
import logging
import pytz
import humanize as hu
import arrow
import re
from cachetools import cached, LRUCache, TTLCache
from collections import namedtuple
from datetime import timedelta, datetime, time, date
from iit.timespan import TimeSpan
from iit.config import config

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
        self._start = arrow.get(start)
        self._end = arrow.get(end)
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

    def does_conflict(self, a_start, a_end):
        a1 = a_start
        a2 = a_end
        e1 = self.start
        e2 = self.end
        assert e1.tzinfo
        assert e2.tzinfo
        assert a1.tzinfo
        assert a2.tzinfo
        return (a1 < e1 and a2 > e2) or (a1 > e1 and a2 < e2) or (a1 < e2 and a2 > e2)




class FreeCalendar(Calendar):
    pass

class BusyCalendar(Calendar):
    pass


class CalendarCollection:
    def __init__(self):
        self.cals : T.Iterable[Calendar] = []

    def add_calendar(self, calendar):
        self.cals.append(calendar)


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def fetch_vobject(url) -> vobject.iCalendar:
    log.debug("Fetching %s", url)
    chunk = bytes()
    try:
        resp = requests.get(url)
        for event in vobject.readComponents(resp.text):
            yield event
    except Exception as e:
        log.error("%s: %s", url, e)
        return


def vevent_to_timeblock(event):
    if "dtend" not in event:
        log.warning("Event missing dtend: %s", event)
        return None
    begin = arrow.get(event["dtstart"][0].value)
    end = arrow.get(event["dtend"][0].value)
    return TimeBlock(begin=begin, end=end)


def get_events_from_vcal(vcal):
    for e in vcal.contents["vevent"]:
        yield e.contents


def get_tz_from_vcal(vcal, default=str(config.my_timezone)) -> pytz.timezone:
    if "x-wr-timezone" not in vcal.contents:
        log.warning("ical does not have x-wr-timzone. Using %s", default)
        return default
    tz: T.AnyStr = vcal.contents["x-wr-timezone"][0].value
    return pytz.timezone(tz)


def construct_collection():
    cfg_cals = {
        "free": config.free_calendars,
        "blocked": config.blocked_calendars,
    }
    collection = CalendarCollection()
    for caltype in ("free", "blocked"):
        for cal in cfg_cals.get(caltype, []) or []:
            for vcal in fetch_vobject(cal):
                tz = get_tz_from_vcal(vcal)
                calendar = FreeCalendar(tz) if caltype == "free" else BusyCalendar(tz)
                for event in get_events_from_vcal(vcal):
                    ev = vevent_to_timeblock(event)
                    if not ev:
                        continue
                    calendar.add_event(event)
                collection.add_calendar(calendar)
    return collection


def top_of_hour(when: datetime):
    arr = arrow.get(when)
    return arr.shift(hours=+1).replace(minute=0, second=0)


def awareness(
    unaware: T.Union[datetime, time], tz=config.my_timezone
) -> T.Union[datetime, time]:
    if unaware.tzinfo:
        return unaware
    return tz.localize(unaware)


def does_conflict(calcol: CalendarCollection, a_start: arrow.Arrow, a_end: arrow.Arrow):
    # Make sure both arrow tzs are aligned.
    a_start = a_start.to(a_end.tzinfo)

    # Align them both to my_timezone
    a_start = a_start.to(config.my_timezone)
    a_end = a_end.to(config.my_timezone)

    swd = config.start_workday
    ewd = config.end_workday

    # run the comparisons
    # To the workweek
    if a_end.time() >= ewd:
        return True
    if a_start.time() <= swd:
        return True

    # check the conflicts with the calendars
    if calcol.does_conflict(a_start, a_end):
        log.debug(
            "Not yielding %s - %s",
            a_start.format("MMM DD HH:mm a"),
            a_end.format("MMM DD HH:mm a"),
        )
        return True
    return False


# def fetch_calblocks(
#     duration: timedelta, inittime=arrow.now(tz=str(config.my_timezone))
# ) -> T.Iterable[TimeSpan]:
#     grace = config.grace_period
#     starttime = top_of_hour(inittime) + grace
#     a1 = starttime
#     collection = construct_collection()
#     endspan = config.get_end_view_dt(inittime)
#     endsequence = starttime + config.view_duration
#     # Now go through each of the `duration` blocks starting at inittime
#     while a1 + duration < endsequence:
#         a2 = a1 + duration
#         # log.debug("Checking for time %s -> %s (duration=%s)", a1, a2, duration)
#         if not does_conflict(collection, a1, a2):
#             yield TimeSpan(a1, a2)
#         a1 = a2


# @cached(LRUCache(1024))
# def calblock_choices(
#     duration: timedelta,
#     year=None,
#     month=None,
#     day=None,
#     inittime=datetime.now(config.my_timezone),
# ) -> T.Iterable[TimeSpan]:
#     """Automagically returns the next choice in the chain given the input.

#     TODO: Somhow this seems wrong; might need improvment

#     Args:
#         duration (timedelta): The duration of the appointment
#         year (int, optional): Chosen year. Defaults to None.
#         month (int, optional): Chosen month. Defaults to None.
#         day (int, optional): Chosen day. Defaults to None.
#         inittime (tz-aware datetime, optional): Initial time. Defaults to datetime.now(get_tz()).

#     Returns:
#         T.Iterable[T.Any]: depending...
#             - list of years if nothing is selected
#             - list of months if year is selected
#             - list of days if month is selected
#             - list of timespans (as json) if day is selected

#     Yields:
#         Iterator[T.Iterable[TimeSpan]]: _description_
#     """
#     for ts in fetch_calblocks(duration, inittime=inittime):
#         ts: TimeSpan
#         if year and ts.start.year == year:
#             yield ts.start.month
#         elif month and ts.start.month == month:
#             yield ts.start.day
#         elif day and ts.start.day == day:
#             yield ts
#         elif not year:
#             yield ts.to_json()
