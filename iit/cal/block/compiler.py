from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.models.block import Block
from sqlalchemy.engine import Engine
from sqlalchemy import func, select
from psycopg2.extras import Range, DateTimeTZRange

from iit.models.block import Session

class BlockCompilerBase:
    
    def __init__(self, start : Arrow, end : Arrow, duration : timedelta, duration_label):
        self.start = start
        self.end = end
        self.duration = duration
        self.duration_label = duration_label
    
    def on_range(self, curr_start: Arrow, curr_end : Arrow):
        raise NotImplementedError()
    
    def compile(self):
        curr_start = self.start
        while curr_start + self.duration < self.end:
            curr_end = curr_start + self.duration
            self.on_range(curr_start, curr_end)
            curr_start = curr_end

class PostgresBlockCompiler(BlockCompilerBase):
    
    def __init__(self, *args, **kwargs):
        super(PostgresBlockCompiler, self).__init__(*args, **kwargs)
    
    def on_range(self, start : Arrow, end : Arrow):
        with Session() as session:
            block = Block(
                name = self.duration_label,
                during = DateTimeTZRange(start.datetime, end.datetime),
            )
            session.add(block)
            session.commit()