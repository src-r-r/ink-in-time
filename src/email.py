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
from email.message import EmailMessage
from uuid import uuid4

import smtplib

from .db import get_db
from .config import config as cfg
from .core import (
    TPL_EML_PARTICIPANT,
    TPL_EML_ORGANIZER,
    TPL_ICS_CAL,
    TPL_ICS_INV,
    ARROW_ICS_FORMAT,
)
from .appointment import Appointment

log = logging.getLogger(__name__)


def render_str(string: T.AnyStr, ctx=dict(), **context):
    return Template(string).render(ctx or context)


class AppointmentRequestBase:
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
        created = arrow.utcnow()
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
            "dtstart": self.start.to("UTC").format(ARROW_ICS_FORMAT),
            "human_end": self.start.format(cfg.ics_dt_format_end),
            "raw_end": self.end,
            "dtend": self.end.to("UTC").format(ARROW_ICS_FORMAT),
            "notes": self.notes,
            "block_key": self.block.id,
            "block_label": self.block.label,
            "raw_duration": self.end - self.start,
            "human_duration": cfg.call_humanize(self.end - self.start),
            "meeting_link": self.meeting_link,
            "created": created.to("UTC").format(ARROW_ICS_FORMAT),
            "uid": self.generate_uid(),
            # TODO: implement n_guests
            "n_guests": 0,
        }
        kw.update(cfg.variables)
        description = cfg.render(self.get_email_content_template(), kw)
        description = description.encode("unicode_escape").decode("utf-8")
        summary = render_str(self.get_subject_template(), kw)
        summary = summary.encode("unicode_escape").decode("utf-8")
        kw.update({"description": description, "summary": summary,})
        # fold in the variables given in the yml
        return kw

    def smtp(self):
        srv = cfg.email_server
        auth_keys = ("username", "password")
        extra = ("use_ssl",)
        conn_kw = dict([(k, v) for (k, v) in srv.items() if k not in auth_keys + extra])
        creds = dict([(k, v) for (k, v) in srv.items() if k in auth_keys])
        log.debug("Connecting to %s", conn_kw)
        if srv.get("use_ssl", True):
            conn = smtplib.SMTP_SSL(**conn_kw)
        else:
            conn = smtplib.SMTP(**conn_kw)
        if creds:
            conn.login(creds["username"], creds["password"])
        return conn
    
    def generate_uid(self):
        return str(uuid4().hex)
    
    def get_cal_ics_template(self):
        raise NotImplementedError()
    
    def get_inv_ics_template(self):
        raise NotImplementedError()
    
    def get_email_content_template(self):
        raise NotImplementedError()
    
    def get_email_to(self):
        raise NotImplementedError()
    
    def get_subject_template():
        raise NotImplementedError()
    
    def get_description(self):
        raise NotImplementedError()

    def get_summary(self):
        return Template(cfg.ics_summary).render(self.get_format_kwargs())

    def create_calendar_ics(self):
        return cfg.render(self.get_cal_ics_template(), self.get_format_kwargs())

    def create_invite_ics(self):
        return cfg.render(self.get_inv_ics_template(), self.get_format_kwargs())

    def get_email_content(self):
        return cfg.render(self.get_email_content_template(), self.get_format_kwargs())

    def create_email(self):
        em = EmailMessage()
        em["Subject"] = Template(self.get_subject_template()).render(
            self.get_format_kwargs()
        )
        em["From"] = cfg.email_from
        em["To"] = self.get_email_to()
        em.set_content(self.get_email_content())
        return em
    
    def add_ics(self, msg, ics, filename):
        bin_ics = ics.encode("utf-8")
        msg.add_attachment(bin_ics, maintype="text", subtype="calendar", filename=filename)

    def send_email(self):
        msg = self.create_email()
        calendar = self.create_calendar_ics()
        invite = self.create_invite_ics()
        self.add_ics(msg, calendar, "calendar.ics")
        # self.add_ics(msg, invite, "invite.ics")
        with self.smtp() as s:
            resp = s.send_message(msg)
            return resp


class OrganizerAppointmentRequest(AppointmentRequestBase):

    def get_description(self):
        return cfg.render(TPL_EML_ORGANIZER, self.get_format_kwargs())

    def get_cal_ics_template(self):
        return TPL_ICS_CAL
    
    def get_inv_ics_template(self):
        return TPL_ICS_INV
    
    def get_email_content_template(self):
        return TPL_EML_ORGANIZER
    
    def get_email_to(self):
        return cfg.organizer_email
    
    def get_subject_template(self):
        return cfg.email_organizer_subject

class ParticipantAppointmentRequest(AppointmentRequestBase):

    def get_description(self):
        return cfg.render(TPL_EML_PARTICIPANT, self.get_format_kwargs())

    def get_cal_ics_template(self):
        return TPL_ICS_CAL
    
    def get_inv_ics_template(self):
        return TPL_ICS_INV
    
    def get_email_content_template(self):
        return TPL_EML_PARTICIPANT
    
    def get_email_to(self):
        return cfg.organizer_email
    
    def get_subject_template(self):
        return cfg.email_organizer_subject