from iit.cal.source import CalendarSource
from iit.cal.event import Event
from datetime import timedelta
import random
import arrow

class MockCalendarSource(CalendarSource):
    
    def __init__(self, start : arrow.Arrow, end : arrow.Arrow):
        self.start = start
        self.end = end
        
    def _rand_interval(self):
        return timedelta(hours=random.randint(10, 30))

    def _rand_duration(self):
        return timedelta(minutes=random.choice([15, 30, 60, 90, 120]))
    
    def get_events(self):
        e_start = self.start
        while e_end <= self.end:
            e_end = self.start + self._rand_duration()
            yield Event(e_start, e_end)
            e_start = e_end + self._rand_interval()
