from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy import select, update, column, literal, cast, func, table
from sqlalchemy.dialects.postgresql import TSTZRANGE
from psycopg2.extras import DateTimeTZRange

from iit.cal.source import CalendarSource
from iit.cal.event import Event
from iit.models.block import Block, Session

import logging
log = logging.getLogger(__name__)

class CalendarCompilerBase:
    def __init__(self, source: CalendarSource):
        self.source = source

    def on_event(self, event: Event):
        raise NotImplementedError()

    def compile(self):
        for event in self.source.get_events():
            self.on_event(event)


class PostgresCalendarCompiler(CalendarCompilerBase):
    def __init__(self, source: CalendarSource):
        super(PostgresCalendarCompiler, self).__init__(source)
    
    def _debug_event(self, event : Event):
        match = (event.start, event.end)
        with Session() as session:
            res = session.query(func.lower(Block.during), func.upper(Block.during))
            avail = res.all()
        with Session() as session:
            execution_options = {"synchronize_session": "fetch"}
            where = (cast(event.as_range(), TSTZRANGE)).op("&&")(cast(column("during"), TSTZRANGE))
            stmt = session.query(Block)
            stmt = stmt.where(where)
            stmt = stmt.count()
            res = stmt
            # res = session.execute(stmt, execution_options=execution_options)
            log.debug("%s->%s should match %s items", event.start, event.end, res)

    def on_event(self, event: Event):
        self._debug_event(event)
        with Session() as session:
            # Basically try to construct a statement like this (because it works!)
            #  UPDATE block
            #    SET is_unavailable=True
            #    WHERE
            #      TSTZRANGE(during) &&
            #      TSTZRANGE(DATE '2016-01-20',
            #                DATE '2016-02-10');
            # session.query(Block).filter(
            #     cast(Block.during, TSTZRANGE).op("&&")(event.as_range())
            # ).update({"is_unavailable": True}, synchronize_session=False)
            execution_options = {"synchronize_session": "fetch"}
            # what = table("block", column("is_unavailable"))
            where = (cast(event.as_range(), TSTZRANGE)).op("&&")(cast(column("during"), TSTZRANGE))
            values = dict(is_unavailable=True)
            stmt = update(Block).where(where).values(**values)
            session.execute(stmt, execution_options=execution_options)
            session.commit()
