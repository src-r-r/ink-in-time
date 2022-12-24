import typing as T
from iit.place.remote_place import RemoteMeetingPlace
import requests

PHONE_NUMBERS = "https://api.jitsi.net/phoneNumberList?conference=%(room_name)s@conference.meet.jit.si"
ROOM_URL = "https://meet.jit.si/%(room_name)s"
CONFERENCE_ID = "https://api.jitsi.net/conferenceMapper?room=%(room_name)s"


class JitsiMeetingPlace(RemoteMeetingPlace):
    def __init__(self, room_name: T.AnyStr = None, *args, **kwargs):
        kwargs.update(
            {
                "url": ROOM_URL % {"room_name": room_name},
            }
        )
        
        self._phone_url = PHONE_NUMBERS % {"room_name": room_name}
        self._conf_id_url = CONFERENCE_ID % {"room_name": room_name}
        # Get a list of phone numbers
        resp = requests.get(self._phone_url)
        assert resp.status_code == 200
        self.phone_numbers = resp.json()["numbers"]
        # Get the conference ID
        resp = requests.get(self._conf_id_url)
        assert resp.status_code == 200
        self.conference_id = resp.json()["id"]
        super(JitsiMeetingPlace, self).__init__(*args, **kwargs)

    def __str__(self):
        return f"<{type(self).__name__} >"

    def __repr__(self):
        return str(self)
