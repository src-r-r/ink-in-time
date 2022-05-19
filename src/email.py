import typing as T
import arrow
import logging
import humanize as hu
from icalendar import Calendar, Event, vCalAddress, vText
import smtplib
from email.contentmanager import ContentManager
from email.message import EmailMessage
from email import encoders
from uuid import uuid4 as _uuid
from jinja2 import Template
import smtplib

from .db import get_db
from .config import config as cfg
from .core import EM_TEMPLATE_PARTICIPANT, EM_TEMPLATE_ORGANIZER
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
        meeting_link: T.AnyStr,
    ):
        self.block = appointment
        self.start = start
        self.end = end
        self.participant_email = participant_email
        self.participant_name = participant_name
        self.notes = notes
        self.meeting_link = meeting_link

    def get_format_kwargs(self):
        kw = {
            "organizer_cn": cfg.organizer_cn,
            "organizer_email": cfg.organizer_email,
            "organizer_role": cfg.organizer_role,
            "organizer_timezone": cfg.my_timezone,
            "participant_timezone": str(self.start.tzinfo),
            "participant_cn": self.participant_name,
            "participant_email": self.participant_email,
            "human_start": self.start.format(cfg.ics_dt_format_start),
            "raw_start": self.start,
            "human_end": self.start.format(cfg.ics_dt_format_end),
            "raw_end": self.end,
            "notes": self.notes,
            "block_key": self.block.id,
            "block_label": self.block.label,
            "raw_duration": self.end - self.start,
            "human_duration": cfg.call_humanize(self.end - self.start),
            "meeting_link": self.meeting_link,
        }
        # fold in the variables given in the yml
        kw.update(cfg.variables)
        return kw

    def smtp(self):
        srv = cfg.email_server
        auth_keys = ("username", "password")
        conn = dict([(k, v) for (k, v) in srv.items() if k not in auth_keys])
        creds = dict([(k, v) for (k, v) in srv.items() if k in auth_keys])
        log.debug("Connecting to %s", conn)
        return smtplib.SMTP(**conn)

    def get_summary(self):
        return Template(cfg.ics_summary).render(self.get_format_kwargs())

    def create_event_organizer(self):
        organizer = vCalAddress(f"MAILTO:{cfg.organizer_email}")
        organizer.params["cn"] = cfg.organizer_cn
        if cfg.organizer_role:
            organizer.params["role"]
        return organizer

    def create_ics_event(self, part_or_org):
        event = Event()
        event.add("summary", self.get_summary())
        event.add("dtstart", self.start.datetime)
        event.add("dtend", self.end.datetime)
        event["organizer"] = self.create_event_organizer()
        event["location"] = vText(self.meeting_link)
        event["uid"] = _uuid().hex
        event["prodid"] = "-//Ink In Time Scheduler//mxm.dk//"
        event["version"] = "2.0"
        event["description"] = self.get_participant_content()
        if part_or_org == "organizer":
            event["description"] = self.get_organizer_content()
        return event

    def create_ics(self, part_or_org):
        cal = Calendar()
        cal.add("attendee", f"MAILTO:{self.participant_email}")
        cal.add_component(self.create_ics_event(part_or_org))
        return cal

    def get_participant_content(self):
        text = EM_TEMPLATE_PARTICIPANT.read_text()
        return Template(text).render(self.get_format_kwargs())

    def get_organizer_content(self):
        text = EM_TEMPLATE_ORGANIZER.read_text()
        return Template(text).render(self.get_format_kwargs())

    def create_participant_email(self):
        from email.message import EmailMessage

        em = EmailMessage()
        em["Subject"] = Template(cfg.email_participant_subject).render(
            self.get_format_kwargs()
        )
        em["From"] = cfg.organizer_email
        em["To"] = self.participant_email
        em.set_content(self.get_participant_content())
        return em

    def create_organizer_email(self):
        em = EmailMessage()
        em["Subject"] = cfg.email_organizer_subject % self.get_format_kwargs()
        em["From"] = cfg.organizer_email
        em["To"] = cfg.organizer_email
        em.set_content(self.get_organizer_content())
        return em

    def attach_ics(self, part_or_org, msg: EmailMessage):
        ics = self.create_ics(part_or_org)
        msg.add_attachment(ics.to_ical(), maintype="text", subtype="calendar")
        return msg

    def send_participant_email(self):
        log.debug("preparing participant email")
        msg = self.create_participant_email()
        msg = attach_ics("participant", msg)
        with self.smtp() as s:
            s.send_message(s)
            log.debug("sent participant email with %s", resp)
            return resp

    def send_organizer_email(self):
        log.debug("preparing organizer email")
        msg = self.create_organizer_email()
        msg = self.attach_ics("organizer", msg)
        with self.smtp() as s:
            resp = s.send_message(msg)
            log.debug("sent organizer email with %s", resp)
            return resp

    def send_emails(self):
        return (self.send_organizer_email(), self.send_participant_email())
