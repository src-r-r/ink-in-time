from sqlalchemy.engine import create_mock_engine
from iit.cal.block.compiler import PostgresBlockCompiler
from iit.cal.compiler import PostgresCalendarCompiler
from iit.mock.cal.source import StaticMockCalendarSource
from datetime import timedelta, datetime, time
from sqlalchemy import func, select, table, column, or_, and_
import arrow
from iit.types import FlexTime

from iit.models.block import Block

def approx_equal(dt1 : datetime, dt2 : datetime, variance=2.0):
    sec1 = dt1.toordinal()
    sec2 = dt2.toordinal()
    return sec1 - variance < sec2 or sec1 + variance > sec2

def test_calendar_compiler(db_session):
    duration = timedelta(minutes=60)
    lower = arrow.Arrow(2021, 1, 1, hour=0)
    upper = arrow.Arrow(2021, 1, 4, hour=0)
    block_compiler = PostgresBlockCompiler(
        db_session,
        lower,
        upper,
        duration,
        "60min",
    )
    block_compiler.compile()
    source = StaticMockCalendarSource(1, 5, 4, 5)
    calendar_compiler = PostgresCalendarCompiler(source)
    calendar_compiler.compile()
    count = db_session.query(Block).filter(Block.is_unavailable == True).count()
    assert count > 0
    # Every block of time not part of the static source
    # should be is_available=True; everything part of the
    # static source should be is_available=False
    where = and_(
        func.lower(column("during")) <= lower.datetime,
        func.upper(column("during")) >= upper.datetime,
    )
    # where = (cast(event.as_range(), TSTZRANGE)).op("&&")(cast(column("during"), TSTZRANGE))
    stmt = select(Block.during, Block.is_unavailable)
    # stmt = stmt.where(where)
    res = db_session.execute(stmt)
    results = res.fetchall()
    assert len(results)
    for (tzrange, is_unavailable) in results:
        (lower, upper) = (arrow.get(tzrange.lower), arrow.get(tzrange.upper))
        assert (approx_equal(lower, FlexTime.get(time(hour=4, minute=0, second=0)).for_today()) and is_unavailable) or (is_unavailable is None)
        assert (approx_equal(lower, FlexTime.get(time(hour=5, minute=0, second=0)).for_today()) and is_unavailable) or (is_unavailable is None)
