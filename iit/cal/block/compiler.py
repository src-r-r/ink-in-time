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
import chalk
from iit.models.block import Session
import logging
log = logging.getLogger(__name__)

DT_FORMAT="%Y-%m-%d, %H:%M %p"

class BlockCompilerBase:
    def __init__(self, start: Arrow, end: Arrow, duration: timedelta, duration_label : T.AnyStr):
        """ Basic block compiler

        :param start: Start window of the block compiler

        :param end: End window of the block compiler

        :param duration: Number of minutes of the block, e.g. 60

        :param duration_label: Label of the appointment, e.g. "Follow-Up"
        """
        self.start = start
        self.end = end
        self.duration = duration
        self.duration_label = duration_label

    def on_range(self, curr_start: Arrow, curr_end: Arrow):
        raise NotImplementedError()

    def compile(self, session):
        log.debug(chalk.underline("Starting at %s"), self.start.strftime(DT_FORMAT))
        curr_start = self.start
        while curr_start + self.duration < self.end:
            curr_end = curr_start + self.duration
            log.debug(chalk.blue("curr_start=%s"), curr_start.strftime(DT_FORMAT))
            self.on_range(session, curr_start, curr_end)
            curr_start = curr_end
        log.debug(chalk.underline("Ending at %s"), self.end.strftime(DT_FORMAT))


class PostgresBlockCompiler(BlockCompilerBase):
    def __init__(self, *args, **kwargs):
        """ Compiler for a postgres database.

        :param start: Start window of the block compiler

        :param end: End window of the block compiler

        :param duration: Number of minutes of the block, e.g. 60

        :param duration_label: Label of the appointment, e.g. "Follow-Up"
        """
        super(PostgresBlockCompiler, self).__init__(*args, **kwargs)

    def on_range(self, session : Session, start: Arrow, end: Arrow):
        name = self.duration_label
        during = DateTimeTZRange(start.datetime, end.datetime)
        if session.query(Block).filter_by(name=name, during=during).count():
            # log.debug("%s already exists, doing nothing", block)
            return
        block = Block(
            name=name,
            during=during,
        )
        session.add(block)
        session.commit()


class PostgresIitBlockCompiler(PostgresBlockCompiler):
    def __init__(
        self,
        weekly_schedule: "WeeklySchedule",
        start_window: T.Optional[Arrow] = None,
        end_window: T.Optional[Arrow] = None,
        *args,
        **kwargs
    ):
        """ Compiler for a postgres database.

        :param weekly_schedule: Weekly schedule to block out certain times.

        :param start: Start window of the block compiler

        :param end: End window of the block compiler

        :param duration: Number of minutes of the block, e.g. 60

        :param duration_label: Label of the appointment, e.g. "Follow-Up"
        """
        """A block compiler for postgres that includes details like a weekly schedule and calendar window.

        Args:
            weekly_schedule (WeeklySchedule): A weekly schedule object to specify daily working hours
            start_window (Arrow): When to start compiling the blocks. Defaults to today if not given.
            end_window (Arrow): When to stop compiling the blocks. Optional. If not given will just pull from the calendar source.
        """
        self.weekly_schedule = weekly_schedule
        super(PostgresIitBlockCompiler, self).__init__(start_window, end_window, *args, **kwargs)

    def on_range(self, session : Session, start: Arrow, end: Arrow):
        if start < self.start or end > self.end:
            # log.debug(
            #     "(%s, %s) outside of range (%s, %s) for block window",
            #     start,
            #     end,
            #     self.start_window,
            #     self.end_window,
            # )
            return
        day_of_week = start.weekday()
        daily_hours: TimeSpan = self.weekly_schedule[day_of_week]
        for span in (daily_hours or []):
            if start.time() < span.start or end.time() > span.end:
                # log.debug(
                #     "(%s, %s) outside of range (%s, %s) for weekday %d",
                #     start.time,
                #     end.time,
                #     span.start,
                #     span.end,
                #     day_of_week,
                # )
                return
        return super(PostgresIitBlockCompiler, self).on_range(session, start, end)
