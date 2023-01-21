import typing as T
import arrow
from iit.cal.event import InboundEvent
from iit.cal.source.base import CalendarSource
from vobject import readComponents
import requests
import logging

if T.TYPE_CHECKING:
    from iit.cal.event import Event

log = logging.getLogger(__name__)


class RemoteCalendarSource(CalendarSource):
    def __init__(self, url):
        self.url = url
        super(CalendarSource, self).__init__()

    def get_events(self) -> T.Iterator["Event"]:
        resp = requests.get(self.url)
        for vCalendar in readComponents(resp.text):
            for vEvent in vCalendar.getSortedChildren():
                if not vEvent.getChildren():
                    continue
                dtstart = vEvent.getChildValue("dtstart")
                dtend = vEvent.getChildValue("dtend")
                duration = vEvent.getChildValue("duration")
                if duration and not dtend:
                    dtend = dtstart + duration
                if not (dtstart and dtend):
                    log.warning("No `start` and `end` for %s", vEvent)
                    continue
                start = arrow.get(dtstart)
                end = arrow.get(dtend)
                yield InboundEvent(start, end)
