import typing as T
from iit.cal.organizer import Organizer

def get_organizer():
    from iit.config import config
    org = config["organizer"]
    cn = org.get("cn", None)
    email = org.get("email")
    role = org.get("role")
    return Organizer(email, cn, role)