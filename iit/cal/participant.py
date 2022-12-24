import typing as T
from iit.cal.member import Member

class Participant(Member):
    pass
    
    def __str__(self):
        cn = self.cn or self.email
        return cn