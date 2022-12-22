try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
from environ import Env

from .core import PACKAGE_NAME, PROJ_DIR, CONFIG_YML, TPL_DIR

env = Env()
env.read_env()

project_name = "Ink In Time"

LOGNAME = __name__

with CONFIG_YML.open("r") as f:
    config = load(f, Loader=Loader)

# other constant settings. I don't like it here. :-(

DB_URL = env.db_url_config("DB_URL")
BROKER_URL = env.url("BROKER_URL")