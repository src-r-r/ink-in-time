import typing as T
import re
import os
from pathlib import Path
from datetime import datetime

from .coreutil import first_config
from environ import Env

env = Env()

# Simple constants

PACKAGE_NAME = "inkintime"

# regular expressions

# https://regex101.com/r/sI6yF5/1
IS_EMAIL = re.compile(
    r"^([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22))*\x40([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d))*$"
).match

# Formatting for dates and times
ARROW_ICS_FORMAT = "YYYYMMDD[T]HHmmSS[Z]"

# System-level files & directories

HERE = Path(__file__).parent.resolve()
ROOT = Path(Path(HERE).resolve().root)

ETC = ROOT / "etc"  # TODO: find windows equiv
ETC_IIT_DIR = ETC / "ink-in-time"
HOME_DIR = Path("~").resolve()

# Project-level files

PROJ_DIR = HERE.parent
PROJ_ENV = HERE / ".env"
HOME_CFG_DIR = HOME_DIR / ".ink-in-time" / "config"
PROJ_CFG_DIR = PROJ_DIR / "config"

# Docker-specific paths
DOCKER_APP = env.path("PROJECT_DIR", PROJ_DIR)

# Config will first try the file pointed at by
# `IIT_YML` (if it exists).
CONFIG_YML = first_config(
    DOCKER_APP, # Used for docker
    ETC_IIT_DIR, # System installs
    HOME_CFG_DIR, # for user installations
    PROJ_CFG_DIR, # Typically for development
    filename="iit.yml",
)


SRC_DIR = PROJ_DIR / "src"
TPL_DIR = SRC_DIR / "templates"

# Templates
# NOTE: These are template **names**, meaning that they're
# passed into a jinja environment (e.g. `cfg.jenv.render`)
TPL_EML_PARTICIPANT = Path("email") / "participant.txt"
TPL_EML_ORGANIZER = Path("email") / "organizer.txt"
TPL_ICS_CAL = Path("ics") / "calendar.ics"
TPL_ICS_INV = Path("ics") / "invite.ics"

# System paths
# NOTE: COMPILEPID_FILE probably not needed.
COMPILEPID_FILE: Path = PROJ_DIR / ".compilepid"

# Mock directory
MOCK_DIR = PROJ_DIR / "mock_data"
MOCK_ICS_DIR = MOCK_DIR / "ics"

# Environment options

FLASK_DEBUG = env.bool("FLASK_DEBUG", False)
FLASK_ENV = env.str("FLASK_ENV", "production")

# Common types
TimeSpan = T.Tuple[datetime, datetime]