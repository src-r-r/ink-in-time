import typing as T
from datetime import datetime, date, time
import pytz
import arrow
import logging
log = logging.getLogger(__name__)

MaybeSpan = T.Tuple[arrow.Arrow | datetime | date]


def arrows_conflict(s1, e1, s2, e2, ref_dt=None, _ref_tz=None):
    """False if span2 conflicts with span1, true otherwise

    Args:
        span1 (T.Tuple[arrow.Arrow]): Tuple of arrows (arrow1, arrow2)
        span2 (T.Tuple[arrow.Arrow]): Tuple of arrows (arrow3, arrow4)
    """
    # Compress the list to make it easier
    arrows: MaybeSpan = [s1, e1, s2, e2]
    # Look for a reference datetime in the span args that have
    #   a timezone
    for (i, a) in enumerate(arrows):
        if not isinstance(a, (time, datetime)):
            raise ValueError("Argument %d (%s) must be a time or datetime.", i, a)
        if isinstance(a, datetime) and a.tzinfo:
            ref_dt = a
    # Fail if no ref_dt with a timezone exists.
    if not ref_dt or not ref_dt.tzinfo:
        raise ValueError("Could not find a datetime with a timezone")
    # Convert all the span args
    for (i, a) in enumerate(arrows):
        # if it's a time, convert it to a datetime with the ref_dt timezone
        if isinstance(a, time):
            arrows[i] = arrow.get(
                year=ref_dt.year,
                month=ref_dt.month,
                day=ref_dt.day,
                hour=a.hour,
                minute=a.minute,
                tzinfo=ref_dt.tzinfo
            )
        # If it's a datetime, convert it to an arrow
        elif isinstance(a, datetime):
            arrows[i] = arrow.get(a)
        # otherwise, convert it to the ref_dt
        else:
            arrows[i].to(datetime.tzname)
    # Now that we're out of the weeds, we can do the comparison
    # expand the list
    (s1, e1, s2, e2) = arrows
    # Make sure the timezones match
    s1 = s1.to(s2.tzinfo)
    e2 = e1.to(e2.tzinfo)
    # Convert things to an timestamp to make it easier
    s1 = s1.timestamp()
    s2 = s2.timestamp()
    e1 = e1.timestamp()
    e2 = e2.timestamp()
    # Do the comparison
    log.debug("%d < %d or %d > %d", s2, e1, e2, s1)
    return (s1 < s2 < e1) or (s1 < e2 < e1)
