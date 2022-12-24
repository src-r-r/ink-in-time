import typing as T
from iit.cal.member import Member

class Organizer(Member):
    
    def __init__(self, email: T.AnyStr, cn : T.AnyStr=None, role : T.AnyStr=None):
        self.email = email
        self.cn = cn
        self.role = role
    
    def __str__(self):
        cn = self.cn or self.email
        if self.role:
            return f"{cn}, {self.role}"
        return cn
