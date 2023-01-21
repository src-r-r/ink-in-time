import typing as T
from sqlalchemy import create_engine, select, distinct
from sqlalchemy.orm import Session

from iit.models.block import Block
from iit.types import TimeSpan
from iit.config import get_config, DB_URL


engine = create_engine(DB_URL)

def find_block_options():
    with Session(engine) as session:
        blocks = session.query(Block.name).distinct().all()
        return [b[0] for b in blocks]

def find_available(*, block: T.AnyStr=None, year: int=None, month: int=None, day: int=None, config=get_config()) -> T.Union[int, TimeSpan]:
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
    
    if not block:
        return config["scheduling"]["appointments"]
    
    if block:
        ext_field = "year"
    if year:
        ext_field = "month"
    if month:
        ext_field = "day"
    if day:
        ext_field = None

    selection = None
    if ext_field:
        selection = distinct(func.extract(ext_field, "from", "timestamp", Block.during))
    else:
        selection = select(Block)
    
    if block:
        stmt = stmt.where(Block.name == block)
    
    with Session(engine) as session:
        session.select(selection)