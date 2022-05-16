import typing as T
from datetime import timedelta


class Appointment:
    
    def __init__(self, id : T.AnyStr, label : T.AnyStr, time : int):
        self.id = id
        self.label = label
        self.time = timedelta(minutes=time)