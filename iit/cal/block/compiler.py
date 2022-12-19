from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.db import Block
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import Range

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
        while curr_start < self.end:
            curr_end = curr_start + self.duration
            self.on_range(self, curr_start, curr_end)
            curr_start = curr_end

class PostgresBlockCompiler(BlockCompilerBase):
    
    def __init__(self, engine : Engine, *args, **kwargs):
        self.bind = engine
        super(PostgresBlockCompiler, self).__init__(*args, **kwargs)
    
    def on_range(self, start : Arrow, end : Arrow):
        with Session(self.bind) as session:
            block = Block(
                name = self.duration_label,
                during = Range(start, end),
            )
            session.add(block)
            session.commit()