import typing as T
from arrow import Arrow
from arrow import now
from datetime import timedelta
from iit.models.block import Block
from iit.types import WeeklySchedule, TimeSpan, FlexTime
from sqlalchemy.engine import Engine
from sqlalchemy import func, select
from psycopg2.extras import Range, DateTimeTZRange
if T.TYPE_CHECKING:
    from iit.cal.weeklyschedule import WeeklySchedule

from iit.models.block import Session
import logging
log = logging.getLogger(__name__)


class BlockCompilerBase:
    def __init__(self, start: Arrow, end: Arrow, duration: timedelta, duration_label : T.AnyStr):
        self.start = start
        self.end = end
        self.duration = duration
        self.duration_label = duration_label

    def on_range(self, curr_start: Arrow, curr_end: Arrow):
        raise NotImplementedError()

    def compile(self):
        curr_start = self.start
        while curr_start + self.duration < self.end:
            curr_end = curr_start + self.duration
            self.on_range(curr_start, curr_end)
            curr_start = curr_end


class PostgresBlockCompiler(BlockCompilerBase):
    def __init__(self, session, *args, **kwargs):
        self.session = session
        super(PostgresBlockCompiler, self).__init__(*args, **kwargs)

    def on_range(self, start: Arrow, end: Arrow):
        name = self.duration_label
        during = DateTimeTZRange(start.datetime, end.datetime)
        block = Block(
            name=name,
            during=during,
        )
        if self.session.query(Block).filter_by(name=name, during=during).count():
            log.debug("%s already exists, doing nothing", block)
            return
        self.session.add(block)
        self.session.commit()


class PostgresIitBlockCompiler(BlockCompilerBase):
    def __init__(
        self,
        weekly_schedule: "WeeklySchedule",
        start_window: T.Optional[Arrow] = None,
        end_window: T.Optional[Arrow] = None,
        *args,
        **kwargs
    ):
        """A block compiler for postgres that includes details like a weekly schedule and calendar window.

        Args:
            weekly_schedule (WeeklySchedule): A weekly schedule object to specify daily working hours
            start_window (Arrow): When to start compiling the blocks. Defaults to today if not given.
            end_window (Arrow): When to stop compiling the blocks. Optional. If not given will just pull from the calendar source.
        """
        self.session = session
        self.weekly_schedule = weekly_schedule
        self.start_window = start_window or now()
        self.end_window = end_window
        super(PostgresWorkingHoursBlockCompiler, self).__init__(*args, **kwargs)

    def on_range(self, start: Arrow, end: Arrow):
        if start < self.start_window or end > self.end_window:
            log.debug(
                "(%s, %s) outside of range (%s, %s) for block window",
                start,
                end,
                self.start_window,
                self.end_window,
            )
            return
        day_of_week = start.weekday()
        daily_hours: TimeSpan = self.weekly_schedule[day_of_week]
        if start.time < daily_hours.start.time or end.time > daily_hours.end.time:
            log.debug(
                "(%s, %s) outside of range (%s, %s) for weekday %d",
                start.time,
                end.time,
                daily_hours.start.time,
                daily_hours.end.time,
                day_of_week,
            )
            return
        return super(PostgresIitBlockCompiler, self).on_range(start, end)
