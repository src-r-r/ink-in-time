import typing as T
import arrow
from datetime import datetime
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import TSTZRANGE
from psycopg2.extras import DateTimeTZRange
from flask import Request
from jinja2 import Template

from iit.place.base import MeetingPlace
from iit.core.organizer import get_organizer

Dtlike = T.Union[datetime, arrow.Arrow]


class EventBase:
    def __init__(
        self,
        start: Dtlike,
        end: Dtlike,
    ):
        self.start = arrow.get(start)
        self.end = arrow.get(end)

    def as_range(self):
        return DateTimeTZRange(self.start.datetime, self.end.datetime)

    def overlaps(self, *other: T.Iterable[T.Any]):
        return self.as_range().overlaps(*other)


class InboundEvent(EventBase):
    def __init__(self, *args, **kwargs):
        super(InboundEvent, self).__init__(*args, **kwargs)

    def __str__(self):
        return f"<{type(self).__name__} >"

    def __repr__(self):
        return str(self)


class OutboundEvent(EventBase):
    def __init__(
        self,
        start: Dtlike,
        end: Dtlike,
        title: T.AnyStr,
        organizer_email: T.AnyStr,
        meeting_place: MeetingPlace,
    ):
        self.title = title
        self.organizer_email = organizer_email
        self.meeting = meeting_place
        super(OutboundEvent, self).__init__(*args, **kwargs)

    def from_post_data(
        self,
        block: T.AnyStr,
        start: Dtlike,
        end: Dtlike,
        request: Request,
        config: T.Hashable,
    ):
        organizer = get_organizer()
        DEFAULT_SUMMARY = (
            "{{ block }} between {{ organizer_cn }} and {{ participant_cn }}"
        )
        title_tpl = config["ics"].get("summary", DEFAULT_SUMMARY)
        title = Template(title_tpl).render(
            dict(
                block=block,
                organizer_cn=str(organizer),
                participant_cn=participant_cn or participant_email,
            )
        )
        return type(self)(start, end, title, organizer_email, meeting_place)

    def __str__(self):
        return f"<{type(self).__name__} >"

    def __repr__(self):
        return str(self)
