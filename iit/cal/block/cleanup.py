from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.models.block import Block
from sqlalchemy.engine import Engine
from sqlalchemy import func, delete, select, cast
from sqlalchemy.orm import Session
import calendar
from psycopg2.extras import Range, DateTimeTZRange
from sqlalchemy.dialects.postgresql import TSTZRANGE, TIMESTAMP

class BlockCleanupBase:
    def __init__(self, threshold: Arrow):
        self.threshold: Arrow = threshold

    def cleanup(self):
        raise NotImplementedError()


class PostgresBlockCleanup(BlockCleanupBase):
    def __init__(self, *args, **kwargs):
        super(PostgresBlockCleanup, self).__init__(*args, **kwargs)

    def cleanup(self, session : Session):
        threshold_epoch = calendar.timegm(self.threshold.timetuple())
        epochs = session.execute(select(func.extract("EPOCH", cast(func.upper(Block.during), TIMESTAMP)).label("epochs"))).scalars().all()
        targets_to_delete = [e for e in epochs if e < threshold_epoch]
        num_to_delete = session.execute(select(func.count(Block.name)).where(func.extract("EPOCH", func.upper(Block.during)) < threshold_epoch)).scalar()
        stmt = delete(Block).where(func.upper(Block.during) < self.threshold.datetime)
        session.execute(stmt, execution_options={"synchronize_session": 'fetch'})
        session.commit()
