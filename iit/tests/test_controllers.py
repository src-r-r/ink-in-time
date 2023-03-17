import pytest
from iit.controllers.block import find_available
from iit.models.database import db
from calendar import monthrange

@pytest.mark.usefixtures("app_ctx")
def test_find_available(block_compiler, calendar_compiler, block_cleanup):
    block = "Full Consultation"
    
    block_compiler.compile(db.session)
    calendar_compiler.compile(db.session)
    block_cleanup.cleanup(db.session)

    year = block_compiler.start.date().year
    low_month = block_compiler.start.date().month
    high_month = block_compiler.end.date().month

    target_day = block_compiler.start.shift(days=5).floor("day")
    target_time = target_day.shift(hours=10)
    
    low_day = block_compiler.start.date().day
    high_day = monthrange(target_day.date().year, target_day.date().month)[-1]

    appts = find_available(db.session)
    assert appts == [
        block,
    ]

    years = find_available(db.session, block=block)
    assert years == [
        year,
    ]

    months = find_available(db.session, block=block, year=year)
    assert months == [m for m in range(low_month, high_month+1)]

    days = find_available(db.session, block=block, year=year, month=target_day.date().month)
    assert days == [m for m in range(low_day, high_day+1)]
