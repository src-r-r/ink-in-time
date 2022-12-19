from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.db import Block
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import Range


class BlockCleanupBase:
    def __init__(self, theshold: Arrow):
        self.theshold: Arrow = theshold

    def cleanup(self):
        raise NotImplementedError()


class PostgresBlockCleanup(BlockCleanupBase):
    def __init__(self, bind: Engine, *args, **kwargs):
        self.bind = bind
        super(PostgresBlockCleanup, self).__init__(*args, **kwargs)

    def cleanup(self):
        with Session(self.bind) as session:
            stmt = select(Block).filter(Block.during < now(self.threshold.tzinfo))
            session.execute(stmt)
            session.flush()
