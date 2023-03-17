from sqlalchemy.engine import create_mock_engine
from iit.cal.block.compiler import PostgresBlockCompiler
from iit.cal.block.cleanup import PostgresBlockCleanup
from datetime import timedelta
from sqlalchemy import func, select
import arrow

from iit.models.block import Block

DT_FORMAT="%Y-%m-%d, %H:%M %p"

def test_block_compiler(db_session):
    start = arrow.now().ceil("hour")
    end = start.shift(days=1)
    duration = timedelta(minutes=30)
    duration_label = "30min"
    db_session.query(Block).delete(synchronize_session=False)
    comp = PostgresBlockCompiler(start, end, duration, duration_label)
    comp.compile(db_session)
    db_session.commit()
    result = db_session.query(func.Count(Block.id))
    nblocks = result[0][0]
    assert(nblocks) > 0
    blocks = db_session.query(Block)
    for (i, block) in enumerate(blocks):
        curr : arrow.Arrow = block.during.upper
        assert curr < end, f"Block {i} of {nblocks} is out of range ({curr.strftime(DT_FORMAT)} >= {end.strftime(DT_FORMAT)})"

def test_block_cleanup(db_session):
    threshold = arrow.Arrow(year=2021, month=1, day=2)
    start = threshold.ceil("hour").shift(days=-1)
    end = threshold.ceil("hour").shift(days=1)
    duration = timedelta(hours=1)
    duration_label = "1hour"
    
    comp = PostgresBlockCompiler(start, end, duration, duration_label)
    comp.compile(db_session)
    result = db_session.query(func.Count(Block.id))
    nblocks1 = result[0][0]
    
    
    cleaner = PostgresBlockCleanup(threshold)
    cleaner.cleanup(db_session)
    result = db_session.query(func.Count(Block.id))
    nblocks2 = result[0][0]
    
    assert nblocks2 < nblocks1