import typing as T
from iit.cal.source.remote import RemoteCalendarSource
from iit.cal.source.writeable import WritableCalendarSource
from etebase import Client, Account

CLIENT_NAME = "ink-in-time"

class EtebaseCalendarSource(RemoteCalendarSource, WritableCalendarSource):
    
    CALENDAR_COLLECTION = ("cyberdyne.calendar")
    
    def __init__(self, username: T.AnyStr, password: T.AnyStr, url: T.AnyStr = None):
        super(EtebaseCalendarSource, self).__init__(url)
        self.client = Client(CLIENT_NAME, self.url)
        self.etebase = Account.login(client, username, password)
    
    def add_meeting(self, meeting : "Meeting"):
        import ipdb; ipdb.set_trace()
    
    def _col_mgr(self):
        return self.etebase.get_collection_manager()
    
    def get_events(self):
        col_mgr = self._col_mgr()
        collections = self._col_mgr().list(self.CALENDAR_COLLECTION)

    def __str__(self):
        return f"<{type(self).__name__} >"
