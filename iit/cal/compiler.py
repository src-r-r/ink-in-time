from sqlalchemy.engine import Engine, select, update
from sqlalchemy.orm import Session
from iit.calendars.source import CalendarSource
from iit.calendars.event import Event
from iit.db import Block

class CalendarCompilerBase:
    
    def __init__(self, source : CalendarSource):
        self.source = source
    
    def on_event(self, event : Event):
        raise NotImplementedError()
    
    def compile(self):
        for event in self.source.get_events():
            self.on_event(event)


class PostgresCalendarCompiler(CalendarCompilerBase):
    
    def __init__(self, source : CalendarSource, bind : Engine):
        self.bind = bind
        super(PostgresCalendarCompiler, self).__init__(source)
    
    def on_event(self, event : Event):
        stmt = update(Block).where(event.overlps(Block.during)).values(is_unavailable=True)
        with Session(self.bind) as session:
            session.execute(stmt)