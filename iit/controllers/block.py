import typing as T
from sqlalchemy import create_engine, select, distinct
from sqlalchemy.orm import Session
from sqlalchemy import func, delete, select, cast, table, column
from sqlalchemy.dialects.postgresql import TSTZRANGE

from iit.models.block import Block
from iit.types import TimeSpan
from iit.config import get_config, DB_URL

import arrow

engine = create_engine(DB_URL)


def find_block_options():
    with Session(engine) as session:
        blocks = session.query(Block.name).distinct().all()
        return [b[0] for b in blocks]


def find_available(
    session,
    *,
    block: T.AnyStr = None,
    year: int = None,
    month: int = None,
    day: int = None,
    config=get_config()
) -> T.Union[int, TimeSpan]:
    """Finds an avialable block based on variable granularity.

    If given a year, will return the months. If given a year and month, will return days.

    Args:
        block (T.AnyStr): Time block name
        year (int): Year
        month (int): Month
        day (int): Day

    Returns:
        T.Union[int, TimeSpan]: _description_
    """

    # if not block:
    # return config["scheduling"]["appointments"]

    ext_field = None

    if block:
        ext_field = "year"
    if year:
        ext_field = "month"
    if month:
        ext_field = "day"
    if day:
        ext_field = None

    if ext_field:
        selection = select(
            distinct(
                func.extract(ext_field, func.lower(cast(Block.during, TSTZRANGE)))
            ).label(ext_field)
        )
        _nofield_selection = select(func.lower(Block.during))
    else:
        selection = select(
            distinct(Block.name),
            func.age(
                func.upper(cast(Block.during, TSTZRANGE())),
                func.lower(cast(Block.during, TSTZRANGE())),
            ).label("duration"),
        )
        _nofield_selection = select(Block.name)

    if block:
        # TODO: the clean up should have removed old blocks.
        selection = selection.where(Block.name == block)
        _nofield_selection = _nofield_selection.where(Block.name == block)

    data = session.execute(selection).all()
    _data2 = session.execute(_nofield_selection).scalars()

    return sorted(data)
