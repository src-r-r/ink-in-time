import typing as T
from pathlib import Path
from yaml import load, dump
from datetime import time, datetime, timedelta
from pytz import timezone
from orderedattrdict import AttrDict
import arrow
import logging
import logging.config
import pytz
from .checker import check_config
from .appointment import Appointment

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

LOGNAME = __name__

HERE = Path(__file__).parent.resolve()
PROJ_DIR = HERE.parent
CONFIG_DIR = PROJ_DIR / "config"
CONFIG_YML = CONFIG_DIR / "iit.yml"


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
            self.appointments[k] = Appointment(k, v["label"], v["time"])

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

        self.email = self._cfg["email"]
        self.LOGGING = self._cfg["logging"]
    
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
    
    def get_end_view_dt(self, when=datetime.now()):
        tz = self.my_timezone
        if not when.tzinfo:
            when = tz.localize(when)
        return when + self.grace_period


config = Config()