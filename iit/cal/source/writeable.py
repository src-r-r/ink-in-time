from iit.cal.source.base import CalendarSource

class WritableCalendarSource(CalendarSource):
    def add_event(self, meeting: "Event"):
        raise NotImplementedError()