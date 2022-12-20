import typing as T
import arrow
from datetime import datetime
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import TSTZRANGE
from psycopg2.extras import DateTimeTZRange


class Event:
    def __init__(
        self, start: T.Union[datetime, arrow.Arrow], end=None, sequence_event=None
    ):
        if not end or sequence_event:
            raise RuntimeError("`end` or `sequence_event` required")
        self.start = arrow.get(start)
        self.end = arrow.get(end)
        self.sequence_event = sequence_event

    def as_range(self):
        return DateTimeTZRange(self.start.datetime, self.end.datetime)

    def overlaps(self, *other: T.Iterable[T.Any]):
        return self.as_range().overlaps(*other)
