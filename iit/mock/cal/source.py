from iit.cal.source import CalendarSource
from iit.cal.event import Event
from datetime import timedelta
import random
import arrow


class StaticMockCalendarSource(CalendarSource):
    def __init__(
        self, day_seq_start, day_seq_end, hour_duration_start, hour_duration_end=None
    ):
        self.day_seq_start = day_seq_start
        self.day_seq_end = day_seq_end
        self.hour_duration_start = hour_duration_start
        self.hour_duration_end = hour_duration_end or hour_duration_start + 1
        super(StaticMockCalendarSource, self).__init__()

    def get_events(self):
        """4 AM will be blocked every morning

        Yields:
            Event: An event that occurs at 4AM between 2021/1/1 and 2021/1/4
                   (inclusive)
        """
        for i in range(self.day_seq_start, self.day_seq_end):
            yield Event(
                arrow.Arrow(2021, 1, i, self.hour_duration_start),
                arrow.Arrow(2021, 1, i, self.hour_duration_end),
            )


class RandomizedMockCalendarSource(CalendarSource):
    def __init__(self, start: arrow.Arrow, end: arrow.Arrow):
        self.start = start
        self.end = end
        super(RandomizedMockCalendarSource, self).__init__()

    def _rand_interval(self):
        return timedelta(hours=random.randint(10, 30))

    def _rand_duration(self):
        return timedelta(minutes=random.choice([15, 30, 60, 90, 120]))

    def get_events(self):
        e_start = self.start
        while e_end <= self.end:
            e_end = self.start + self._rand_duration()
            yield Event(e_start, e_end)
            e_start = e_end + self._rand_interval()
