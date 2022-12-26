import typing as T
from iit.callang.parser import DayListParser, TimeListParser, DAYS_ORDER

from iit.types import WeeklySchedule, TimeSpan


def get_workweek(config: T.Hashable = None) -> WeeklySchedule:
    if config is None:
        from iit.config import config as cfg

        config = cfg
    dlp = DayListParser()
    tlp = TimeListParser()
    work_week = config["scheduling"]["work_week"]
    _work_week = dict([(k, []) for k in DAYS_ORDER])
    for (days_text, times_text) in work_week:
        for day in dlp.parse(days_text).normalized():
            for tr in tlp.parse(times_text).normalized():
                _work_week[day._norm_name].append(
                    TimeSpan(
                        tr.start._as_time(),
                        tr.end._as_time(),
                    )
                )
    return WeeklySchedule(**_work_week)
