import typing as T
import arrow
from sqlalchemy.dialects.postgresql import Range

class Event:
    def __init__(self, start : datetime, end=None, sequence_event=None):
        if not end or sequence_event:
            raise RuntimeError("`end` or `sequence_event` required")
        self.calendar = calendar
        self.start = arrow.get(start)
        self.end = arrow.get(end)
        self.sequence_event = sequence_event
    
    def as_range(self):
        return Range(self.start, self.end)
    
    def overlaps(self, *other : T.Iterable[T.Any]):
        return self.as_range().overlaps(*other)