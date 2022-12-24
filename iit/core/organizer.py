import typing as T
from iit.config import config
from iit.cal.organizer import Organizer

def get_organizer():
    org = config["organizer"]
    cn = org.get("cn", None)
    email = org.get("email")
    role = org.get("role")
    return Organizer(email, cn, role)