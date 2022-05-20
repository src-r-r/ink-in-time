import typing as T
from pathlib import Path
from yaml import load, dump
from datetime import time, datetime, timedelta
from pytz import timezone
from orderedattrdict import AttrDict
import humanize
import arrow
import logging
import logging.config
import pytz
from .checker import check_config
from .appointment import Appointment
import importlib

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from .core import PROJ_DIR, CONFIG_YML


project_name = "Ink In Time"

LOGNAME = __name__
class Config:

    def __init__(self, yml=CONFIG_YML):
        with yml.open("r") as f:
            self._cfg = load(f, Loader=Loader)
        
        check_config(self._cfg)
        
        sched = self._cfg["scheduling"]
        self.grace_period = timedelta(**sched["grace_period"])
        self.my_timezone = pytz.timezone(sched["my_timezone"])
        self.start_workday = time(**sched["workday"]["start"])
        self.end_workday = time(**sched["workday"]["end"])
        self.view_duration = timedelta(**sched["view_duration"])

        self.appointments = {}
        for (k, v) in sched["appointments"].items():
            self.appointments[k] = Appointment(k, v["label"], v["time"], v.get("icon"))

        database = self._cfg["database"] 
        cnfpath = database["path"]
        if "{proj_dir}" in cnfpath:
            cnfpath = cnfpath.format(proj_dir=PROJ_DIR)
        dbpath = Path(cnfpath).resolve()
        dbpath.parent.mkdir(exist_ok=True, parents=True)
        self.dbpath = dbpath
        self.database_path = dbpath

        self.db_compilation_interval = timedelta(**database["compilation_interval"])

        self.free_calendars = self._cfg["calendars"]["free"]
        self.blocked_calendars = self._cfg["calendars"]["blocked"]

        cls = self._cfg["email"]["meeting_link_generator"]
        module_name, class_name = cls.split(":")
        _mod = importlib.import_module(module_name)
        self.MeetingGenClass = getattr(_mod, class_name)

        self.organizer_cn = self._cfg["organizer"]["cn"]
        self.organizer_email = self._cfg["organizer"]["email"]
        self.organizer_role = self._cfg["organizer"].get("role")

        self.email_server = self._cfg["email"]["server"]
        self.email_organizer_subject = self._cfg["email"]["organizer"]["subject"]
        self.email_participant_subject = self._cfg["email"]["participant"]["subject"]
        
        self.LOGGING = self._cfg["logging"]

        self.ics_summary = self._cfg["ics"]["summary"]
        self.ics_dt_format_start = self._cfg["ics"]["dt_format"]["start"]
        self.ics_dt_format_end = self._cfg["ics"]["dt_format"]["end"]

        self._humanize_func = self._cfg["ics"].get("humanize_function", "precisedelta")

        self.backref_url = None
        self.backref_label = None
        if "site" in self._cfg and "backref" in self._cfg["site"]:
            self.backref_url = self._cfg["site"]["backref"]["url"]
            self.backref_label = self._cfg["site"]["backref"]["label"]
        
        self.variables = self._cfg.get("variables", {})
    
    def get_working_hours(self, ref_dt : arrow.Arrow):
        """Get the working hours for a given datetime

        Args:
            dt (date): The day for which we'll get the working hours
            _tz (pytz.timezone, optional): pytz.timezone. Defaults to the current user's timezone. Normally should not be specified.
        """
        tz = ref_dt.timezone
        if not tz:
            raise ValueError("ref_dt with timezone needed.")

        st = self.start_workday
        et = self.end_workday

        # Use my_timezone as the base reference & convert to
        # ref_dt after
        tz = self.my_timezone

        # Update the arrow date with the start & end time
        s = ref_dt.replace(hour=st.hour, minute=st.minute, tzinfo=tz)
        e = ref_dt.replace(hour=et.hour, minute=et.minute, tzinfo=tz)

        s = s.to(ref_dt.tzinfo)
        e = e.to(ref_dt.tzinfo)
        
        return (s, e)
    
    def call_humanize(self, *args, **kwargs):
        fnc = getattr(humanize, self._humanize_func)
        return fnc(*args, **kwargs)
    
    def get_end_view_dt(self, when=datetime.now()):
        tz = self.my_timezone
        if not when.tzinfo:
            when = tz.localize(when)
        return when + self.grace_period


config = Config()