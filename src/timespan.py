import humanize as hu
from datetime import datetime
import logging
import arrow
import pytz
log = logging.getLogger(__name__)

class TimeSpan:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    @property
    def duration(self):
        return self.end - self.start
    
    def as_select_value(self):
        start = int(self.start.timestamp())
        end = int(self.end.timestamp())
        return f"{start};{end}"

    def to_json(self):
        return {
            "start": {
                "hour": self.start.hour,
                "minute": self.start.minute,
            },
            "end": {
                "hour": self.end.hour,
                "minute": self.end.minute,
            },
            "duration_in_secs": self.duration.total_seconds(),
            "for_select": self.as_select_value(),
            "human": {
                "duration": hu.precisedelta(self.duration),
                "start": self.start.strftime("%I:%M %P %Z"),
                "end": self.end.strftime("%I:%M %P %Z"),
            }
        }

    def __str__(self):
        s = self.start.strftime("%Y/%m/%d %H:%M")
        e = self.end.strftime("%Y/%m/%d %H:%M")
        d = hu.precisedelta(self.duration)
        return f"{s} -> {e} ({d})"

    def __repr__(self):
        return f"<TimeSpan (start={self.start}, end={self.end}, [duration={self.duration}])>"