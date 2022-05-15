import typing as T
from pathlib import Path
from yaml import load, dump
from datetime import time, datetime, timedelta
from pytz import timezone
import logging
import logging.config
import pytz

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

LOGNAME = __name__

HERE = Path(__file__).parent.resolve()
PROJ_DIR = HERE.parent
CONFIG_DIR = PROJ_DIR / "config"
CONFIG_YML = CONFIG_DIR / "iit.yml"


with CONFIG_YML.open("r") as f:
    config = load(f, Loader=Loader)


def get_tz():
    return pytz.timezone(config["timezone"])


def get_start_workday():
    tz = get_tz()
    t = time(**config["workday"]["start"])
    return t


def get_end_workday():
    tz = get_tz()
    t = time(**config["workday"]["end"])
    return t


def get_timespan():
    return timedelta(**config["timespan"])


def get_grace_period():
    return timedelta(**config["grace_period"])


def get_end_view(when=datetime.now()):
    tz = get_tz()
    if not when.tzinfo:
        when = tz.localize(when)
    return when + get_grace_period()
