import typing as T
import arrow
import logging
import humanize as hu
from icalendar import Calendar, Event, vCalAddress, vText

from .db import get_db
from .config import INVITATION_TEMPLATE ,config as cfg
from .appointment import Appointment

log = logging.getLogger(__name__)


class AppointmentRequest:
    def __init__(
        self,
        appointment: Appointment,
        start: arrow.Arrow,
        end: arrow.Arrow,
        participant_email: T.AnyStr,
        participant_name: T.AnyStr,
        notes: T.AnyStr,
        meeting_link : T.AnyStr,
    ):
        self.block = block
        self.start = start
        self.end = end
        self.participant_email = participant_email
        self.participant_name = participant_name
        self.notes = notes
        self.meeting_link = meeting_link
    
    def get_format_kwargs(self):
        return {
            "organizer_cn": cfg.organizer_cn,
            "organizer_email": cfg.organizer_email,
            "organizer_role": cfg.organizer_role,
            "organizer_timezone": cfg.organizer_timezone,
            "participant_cn": self.participant_name,
            "participant_email": self.participant_email,
            "human_start": self.start.format(cfg.ics_dt_format),
            "raw_start": self.start,
            "human_end": self.start.format(cfg.ics_dt_format),
            "raw_end": self.end,
            "notes": self.notes,
            "block_key": self.block.id,
            "block_label": self.block.label,
            "raw_duration": end - start,
            "human_duration": cfg.call_humanize(end - start),
            "meeting_link": self.meeting_link,
        }
    
    def get_summary(self):
        return cfg.ics_summary % self.get_format_kwargs()

    def create_ics(self):
        cal = Calendar()
        cal.add("attendee", f"MAILTO:{self.participant_email}")

        organizer = vCalAddress(f"MAILTO:{cfg.organizer_email}")
        organizer.params["cn"] = cfg.organizer_cn
        if cfg.organizer_role:
            organizer.params["role"]
        cal.add("summary", self.get_summary())
        cal.add("dtstart", self.start)
        cal.add("dtend", self.end)
        return cal
    
    def create_email(self):
        pass