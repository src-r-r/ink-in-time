from yaml import load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from environ import Env

from iit.core.const import PACKAGE_NAME, PROJ_DIR, CONFIG_YML, TPL_DIR

env = Env()
env.read_env()

project_name = "Ink In Time"

LOGNAME = __name__


def get_config():
    with open(CONFIG_YML, "r") as f:
        config = load(f, Loader=Loader)
    return config


# other constant settings. I don't like it here. :-(

DB_URL = env.str("DB_URL")
BROKER_URL = env.url("BROKER_URL")
