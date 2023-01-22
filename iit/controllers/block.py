import typing as T
from sqlalchemy import create_engine, select, distinct
from sqlalchemy.orm import Session
from sqlalchemy import func, delete, select, cast, table, column
from sqlalchemy.dialects.postgresql import TSTZRANGE

from iit.models.block import Block
from iit.types import TimeSpan
from iit.config import get_config, DB_URL

engine = create_engine(DB_URL)

def find_block_options():
    with Session(engine) as session:
        blocks = session.query(Block.name).distinct().all()
        return [b[0] for b in blocks]

def find_available(session, *, block: T.AnyStr=None, year: int=None, month: int=None, day: int=None, config=get_config()) -> T.Union[int, TimeSpan]:
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
    from iit.models.block import Block
    
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
        query_args = distinct(func.extract(ext_field, func.lower(cast(column("during"), TSTZRANGE))))
    else:
        query_args = distinct(Block.name)

    stmt = session.query(query_args)
    
    if block:
        selection = stmt.filter(Block.name==block)
    
    session.query()
    
    return [s[0] for s in stmt.all()]