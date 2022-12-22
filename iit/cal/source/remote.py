import typing as T
from iit.cal.event import Event
from iit.cal.source.base import CalendarSource
from vobject import readComponents

class RemoteCalendarSource(CalendarSource):
    def __init__(self, url):
        self.url = url
        super(CalendarSource, self).__init__()

    def get_events(self) -> T.Iterator[Event]:
        resp = requests.get(self.url)
        for vCalendar in readComponents(resp.text):
            for vEvent in vCalendar.getSortedChildren():
                start = arrow.get(vEvent.getChildValue("dtstart"))
                end = arrow.get(vEvent.getChildValue("dtend"))
                if not (start and end):
                    log.warning("No `start` or `end` for %s", vEvent)
                    continue
                yield Event(start, end)