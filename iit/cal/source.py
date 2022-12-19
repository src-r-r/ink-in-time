import typing as T
from vobject import iCalendar, readComponents
import requests
from iit.calendars.event import Event

######
# Extracting a calendar source allows for easier unit
# testing. :-)
# 
class CalendarSource:
    
    def get_events(self) -> T.Generator[Event]:
        raise NotImplementedError()

class RemoteCalendarSource(CalendarSource):
    
    def __init__(self, url):
        self.url = url
    
    def get_events(self) -> T.Generator[Event]:
        resp = requests.get(self.url)
        for vEvent in readComponents(resp.text):
            import ipdb; ipdb.set_trace()
            # yield event