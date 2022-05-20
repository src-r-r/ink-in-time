import re
import os
from pathlib import Path

from .coreutil import first_config
from environ import Env

env = Env()

# regular expressions

# https://regex101.com/r/sI6yF5/1
IS_EMAIL = re.compile(
    r"^([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22))*\x40([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d))*$"
).match

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
EM_TEMPLATE_PARTICIPANT = TPL_DIR / "email" / "participant.txt"
EM_TEMPLATE_ORGANIZER = TPL_DIR / "email" / "organizer.txt"

COMPILEPID_FILE: Path = PROJ_DIR / ".compilepid"

MOCK_DIR = PROJ_DIR / "mock_data"
MOCK_ICS_DIR = MOCK_DIR / "ics"
