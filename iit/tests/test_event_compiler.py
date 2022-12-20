from sqlalchemy.engine import create_mock_engine
from iit.cal.block.compiler import PostgresBlockCompiler
from iit.cal.compiler import PostgresCalendarCompiler
from iit.mock.cal.source import StaticMockCalendarSource
from datetime import timedelta
from sqlalchemy import func, select, table, column, or_, and_
import arrow

from iit.models.block import Block


def test_calendar_compiler(Session):
    duration = timedelta(minutes=60)
    lower = arrow.Arrow(2021, 1, 1, hour=0)
    upper = arrow.Arrow(2021, 1, 4, hour=0)
    block_compiler = PostgresBlockCompiler(
        lower,
        upper,
        duration,
        "60min",
    )
    block_compiler.compile()
    source = StaticMockCalendarSource(1, 5, 4, 5)
    calendar_compiler = PostgresCalendarCompiler(source)
    calendar_compiler.compile()
    with Session() as session:
        count = session.query(Block).filter(Block.is_unavailable == True).count()
        assert count > 0
    # Every block of time not part of the static source
    # should be is_available=True; everything part of the
    # static source should be is_available=False
    with Session() as session:
        where = and_(
            func.lower(column("during")) <= lower.datetime,
            func.upper(column("during")) >= upper.datetime,
        )
        # where = (cast(event.as_range(), TSTZRANGE)).op("&&")(cast(column("during"), TSTZRANGE))
        stmt = select(Block.during, Block.is_unavailable)
        # stmt = stmt.where(where)
        res = session.execute(stmt)
        results = res.fetchall()
        assert len(results)
        for (tzrange, is_unavailable) in results:
            (lower, upper) = (tzrange.lower, tzrange.upper)
            assert (lower.hour == 4 and upper.hour == 5 and is_unavailable) or (
                is_unavailable is None
            )
