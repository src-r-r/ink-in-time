from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.models.block import Block
from sqlalchemy.engine import Engine
from sqlalchemy import func, delete, select
from psycopg2.extras import Range, DateTimeTZRange

from iit.models.functions import lower


class BlockCleanupBase:
    def __init__(self, threshold: Arrow):
        self.threshold: Arrow = threshold

    def cleanup(self):
        raise NotImplementedError()


class PostgresBlockCleanup(BlockCleanupBase):
    def __init__(self, session, *args, **kwargs):
        self.session = session
        super(PostgresBlockCleanup, self).__init__(*args, **kwargs)

    def cleanup(self):
        stmt = delete(Block).where(lower(Block.during) < self.threshold.datetime)
        self.session.execute(stmt, execution_options={"synchronize_session": 'fetch'})
        self.session.commit()
