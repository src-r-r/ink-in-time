from sqlalchemy.engine import create_mock_engine
from iit.cal.block.compiler import PostgresBlockCompiler
from iit.cal.block.cleanup import PostgresBlockCleanup
from datetime import timedelta
from sqlalchemy import func, select
import arrow

from iit.models.block import Block


def test_block_compiler(db_session):
    start = arrow.now().ceil("hour")
    end = start.shift(days=1)
    duration = timedelta(minutes=30)
    duration_label = "30min"
    comp = PostgresBlockCompiler(db_session, start, end, duration, duration_label)
    comp.compile()
    result = db_session.query(func.Count(Block.id))
    nblocks = result[0][0]
    assert(nblocks) > 0
    blocks = db_session.query(Block)
    for (i, block) in enumerate(blocks):
        assert block.during.upper < end, f"Block {i} of {nblocks} is too high!"

def test_block_cleanup(db_session):
    threshold = arrow.Arrow(year=2021, month=1, day=2)
    start = threshold.ceil("hour").shift(days=-1)
    end = threshold.ceil("hour").shift(days=1)
    duration = timedelta(hours=1)
    duration_label = "1hour"
    
    comp = PostgresBlockCompiler(db_session, start, end, duration, duration_label)
    comp.compile()
    result = db_session.query(func.Count(Block.id))
    nblocks1 = result[0][0]
    
    
    cleaner = PostgresBlockCleanup(db_session, threshold)
    cleaner.cleanup()
    result = db_session.query(func.Count(Block.id))
    nblocks2 = result[0][0]
    
    assert nblocks2 < nblocks1