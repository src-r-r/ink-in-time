import typing as T
from datetime import timedelta

import psycopg2.extras
import celery
import arrow
from cachetools import cached, LRUCache, TTLCache
from celery import Celery

from iit.config import BROKER_URL, DB_URL
from iit.cal.compiler import PostgresCalendarCompiler
from iit.cal.block.compiler import PostgresBlockCompiler
from iit.cal.block.cleanup import PostgresBlockCleanup
from iit.cal.source.source_factory import get_sources
from iit.tasks.task_loader import get_tasks
from iit.calendar import (
    fetch_calblocks,
    top_of_hour,
    construct_collection,
    get_tz_from_vcal,
    get_events_from_vcal,
)
from iit.db import Block
from iit.timespan import TimeSpan
import logging
log = logging.getLogger(__name__)

app = Celery('inkintime', broker=BROKER_URL)

@app.task
@cached(LRUCache(1024))
def compile_calendars(
    config: T.Hashable,
    CalendarCompiler=PostgresCalendarCompiler,
    BlockCompiler=PostgresBlockCompiler,
    BlockCleanup=PostgresBlockCleanup,
):
    engine = create_engine(DB_URL, echo=True, future=True)
    grace_value = config["scheduling"].get("grace_period", 6)
    grace = timedelta(hours=grace_value)

    view_window = config["scheduling"].get("view_window", {"days": 180})

    start_window = top_of_hour(arrow.now()) + grace
    end_window = start_window + timedelta(**view_window)

    appointments = config["scheduling"]["appointments"]
    for (label, duration_in_minutes) in appointments.items():
        log.debug("Compiling blocks for '%s' (%d minutes)", label, duration_in_minutes)
        duration = timedelta(minutes=duration_in_minutes)
        block_compiler = BlockCompiler(
            start=start_window, end=end_window, duration=duration, duration_label=label
        )
        block_compiler.compile()
        log.debug("[DONE] block compiling")
    log.debug("Clening up blocks")
    cleanup = BlockCleanup()
    cleanup.cleanup()
    log.debug("[DONE] block cleanup")
    for source in get_sources(config):
        log.debug("Compiling from source %s", source)
        calendar_compiler = PostgresCalendarCompiler(source)
        calendar_compiler.compile()
        log.debug("[DONE] compiling calendar source")