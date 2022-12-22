import typing as T
from vobject import iCalendar, readComponents
import requests
from iit.cal.event import Event
import arrow

######
# Extracting a calendar source allows for easier unit
# testing. :-)
#
class CalendarSource:
    def get_events(self) -> T.Iterator[Event]:
        raise NotImplementedError()


