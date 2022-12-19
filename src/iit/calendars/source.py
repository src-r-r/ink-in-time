from vobject import iCalendar

######
# Extracting a calendar source allows for easier unit
# testing. :-)
# 
class CalendarSource:
    
    def get_calendar(self) -> iCalendar:
        raise NotImplementedError()