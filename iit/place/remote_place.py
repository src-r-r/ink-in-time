import typing as T
from iit.place.base import MeetingPlace
class RemoteMeetingPlace(Place):
    
    def __init__(self, url : T.AnyStr):
        self.url = url
        super(RemoteMeetingPlace, self).__init__()