try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from .core import PACKAGE_NAME, PROJ_DIR, CONFIG_YML, TPL_DIR


project_name = "Ink In Time"

LOGNAME = __name__

with CONFIG_YML.open("r") as f:
    config = load(f, Loader=Loader)
