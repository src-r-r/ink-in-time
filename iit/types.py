import typing as T
import humanize as hu
from datetime import datetime, time, timedelta
import logging
import arrow
import pytz

log = logging.getLogger(__name__)

TimeLike = T.Union[arrow.Arrow, time]


class FlexTime(time):
    def for_today(self):
        now = datetime.now()
        return datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    def __sub__(self, o):
        return self.for_today() - o.for_today()

    @classmethod
    def get(cls, tm: time):
        return cls(
            hour=tm.hour, minute=tm.minute, second=tm.second, microsecond=tm.microsecond
        )


class TimeSpan:
    def __init__(
        self, start: TimeLike, end: TimeLike, start_format="h:mm a", end_format="h:mm a"
    ):
        self.start = FlexTime.get(start)
        self.end = FlexTime.get(end)
        self.start_format = start_format
        self.end_format = end_format

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
                "start": self.start.format(self.start_format),
                "end": self.end.format(self.end_format),
                "timezone": self.end.strftime("%Z"),
            },
        }

    def __str__(self):
        s = self.start.strftime("%Y/%m/%d %H:%M")
        e = self.end.strftime("%Y/%m/%d %H:%M")
        d = hu.precisedelta(self.duration)
        return f"{s} -> {e} ({d})"

    def __repr__(self):
        return f"<TimeSpan (start={self.start}, end={self.end}, [duration={hu.naturaldelta(self.duration)}])>"
    

    def __eq__(self, o):
        return isinstance(o, type(self)) and self.start == self.end
    
    def __ne__(self, o):
        return not (self.__eq__(o))


DaySched = T.Optional[T.Tuple[TimeSpan]]

WeeklySchedule = T.NamedTuple(
    "WeeklySchedule",
    sunday=DaySched,
    monday=DaySched,
    tuesday=DaySched,
    wednesday=DaySched,
    thursday=DaySched,
    friday=DaySched,
    saturday=DaySched,
)
