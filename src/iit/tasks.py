import typing as T
import arrow
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql.ranges import sqltypes
from sqlalchemy.dialects.postgresql import Range

import psycopg2.extras
import celery

from cachetools import cached, LRUCache, TTLCache

from iit.calendar import (
    fetch_calblocks,
    top_of_hour,
    construct_collection,
    get_tz_from_vcal,
    get_events_from_vcal,
)
from iit.db import Block
from iit.timespan import TimeSpan


@celery.shared_task
@cached(LRUCache(1024))
def compile_calendars(config: T.Hashable):
    """Compile the calendars & blocks together

    This is supposed to behave like a task qeue, but minimized.

    Args:
        request (flask.Request, optional): Only used to keep flask happy. Defaults to None.
    """
    engine = create_engine(config["database"]["url"], echo=True, future=True)
    grace_value = config["scheduling"].get("grace_period", 6)
    grace = timedelta(hours=grace_value)

    view_window = config["scheduling"].get("view_window", {"days": 60})

    start_window = top_of_hour(arrow.now()) + grace
    end_window = start_window + timedelta(**view_window)

    # TODO: split calendar colleciton and block allocation into 2 threads

    # Collect the events from the calendar
    events = {
        "free": [],
        "blocked": [],
    }
    for resource_type in ("free", "blocked"):
        for resource_url in config["calendars"][resource_type]:
            vcal = fetch_vobject(resource_url)
            tz = get_tz_from_vcal(vcal)
            events[resource_type].extend(get_events_from_vcal(vcal))

    # Update the appointment blocks.
    for (apt_label, apt_spec) in config["scheduling"]["appointments"].items:
        duration: int = appt_spec["time"]
        # clean up any blocks in the past.
        with Session(engine) as session:
            session.execute(
                delete(Block)
                .where(duration=duration)
                .where(Block.start < start_window - timedelta(minutes=duration))
            )
            session.flush()
        # get the latest time block. On the first run this will be
        # the start_window, but on subsequent runs it won't.
        with Session(engine) as session:
            latest_block = (
                session.query(Block).filter_by(name=apt_label).order_by(Block.start)
            )
        # fill out the remaining time blocks.
        _start_time = latest_block.start + duration
        curr_time = _start_time
        with Session(engine) as session:
            while curr_time < end_window + duration:
                block = Block(
                    name=apt_label, during=Range(curr_time, curr_time + duration)
                )
                session.add(block)
                curr_time = curr_time + duration
            session.commit()

    with Session(engine) as session:
        for event in events["blocked"]:
            begin = arrow.get(event["dtstart"][0].value)
            end = arrow.get(event["dtend"][0].value)
            event_range = Range(begin, end)
            stmt = (
                update(Block)
                .where(event_range.overlaps(Block.during))
                .values(is_unavailable=True)
            )
            session.execute(stmt)
