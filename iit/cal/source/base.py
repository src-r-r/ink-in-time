import typing as T
from vobject import iCalendar, readComponents
import requests
import arrow
if T.TYPE_CHECKING:
    from iit.cal.event import Event

######
# Extracting a calendar source allows for easier unit
# testing. :-)
#
class CalendarSource:
    def get_events(self) -> T.Iterator["Event"]:
        raise NotImplementedError()


