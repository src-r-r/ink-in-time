import typing as T
from datetime import timedelta
from celery import Task
import logging
from pathlib import Path
from iit.core import TPL_DIR

from iit.cal.source.source_factory import get_sources
from iit.cal.source.writeable import WritableCalendarSource
from iit.cal.event import Event

log = logging.getLogger(__name__)


class SetFollowupReminders(Task):

    DEFAULT_INTERVAL = timedelta(days=7)
    
    JSON_TEMPLATE = TPL_DIR / "followup-event.json"

    def __init__(
        self, count: int = 1, interval: timedelta = DEFAULT_INTERVAL, *args, **kwargs
    ):
        self.count = count
        self.interval = interval
        super(SendEmailInvite, self).__init__()
    
    def get_event(self, curr_count : int):
        return

    def run(self, config : T.Hashable):
        for source in get_sources(config):
            if not isinstance(source, WritableCalendarSource):
                continue
            source : WritableCalendarSource
            source.add_event(event)
