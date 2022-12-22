import typing as T
from collections import namedtuple
from iit.timespan import TimeSpan

WeeklySchedule: T.NamedTuple(
    "WeeklySchedule",
    sunday=TimeSpan,
    monday=TimeSpan,
    tuesday=TimeSpan,
    wednesday=TimeSpan,
    thursday=TimeSpan,
    friday=TimeSpan,
    saturday=TimeSpan,
)
