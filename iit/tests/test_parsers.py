from datetime import time
import pytest
from simple_chalk import red
from iit.callang.parser import (
    Day,
    Dash,
    Comma,
    CallangTokenError,
    Tokenizer,
    DayList,
    DayListParser,
    TimeListParser,
    TimeList,
    TimeRange,
    TimeVal,
    Merid,
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY,
    SUNDAY,
)
import logging
log = logging.getLogger(__name__)

def test_tokenizer():
    tests = [
        ("mon - fri", [Day("mon"), Dash("-"), Day("fri")]),
        (("m - f"), [Day("m"), Dash("-"), Day("f")]),
        ("moNDay", [Day("moNDay")]),
        (
            "monday, tue, th",
            [Day("monday"), Comma(","), Day("tue"), Comma(","), Day("th")],
        ),
        (("8AM - 4PM"), ([TimeVal("8"), Merid("AM"), Dash("-"), TimeVal("4"), Merid("PM")])),
    ]
    invalid = [
        "mon __&",
        "tu***es",
        "wed+=",
    ]

    tokenizer = Tokenizer()

    for (t, expected) in tests:
        result = [i for i in tokenizer.iter_tokens(t)]
        assert expected == result

    for inv in invalid:
        with pytest.raises(CallangTokenError):
            [t for t in tokenizer.iter_tokens(inv)]


def test_day_list():
    dlp = DayListParser()
    assert dlp.parse("monday") == DayList(Day("monday"))
    assert dlp.parse("m - w").normalized() == DayList(
        Day(MONDAY), Day(TUESDAY), Day(WEDNESDAY)
    )
    assert dlp.parse("m, t, f").normalized() == DayList(
        Day(MONDAY), Day(TUESDAY), Day(FRIDAY)
    )
    assert dlp.parse("m, t-h, f, sun").normalized() == DayList(
        Day(MONDAY),
        Day(TUESDAY),
        Day(WEDNESDAY),
        Day(THURSDAY),
        Day(FRIDAY),
        Day(SUNDAY),
    )


def test_get_time_tokens():

    tokenizer = Tokenizer()

    assert [t for t in tokenizer.iter_tokens("8AM")] == [TimeVal("8"), Merid("AM")]
    assert [t for t in tokenizer.iter_tokens("8AM - 4PM")] == [
        TimeVal("8"),
        Merid("AM"),
        Dash("-"),
        TimeVal("4"),
        Merid("PM"),
    ]
    result = [t for t in tokenizer.iter_tokens("8AM - 11AM, 12PM - 6PM")]
    expected = [
        TimeVal("8"),
        Merid("AM"),
        Dash("-"),
        TimeVal("11"),
        Merid("AM"),
        Comma(","),
        TimeVal("12"),
        Merid("PM"),
        Dash("-"),
        TimeVal("6"),
        Merid("PM"),
    ]
    assert result == expected


def test_time_list():
    tlp = TimeListParser()
    result = tlp.parse("8AM").normalized()
    expected = TimeList(TimeVal("8")).normalized()
    assert result == expected

    log.debug(red("testing '8 - 4PM'"))
    result = tlp.parse("8 - 4PM").normalized()
    expected = TimeList(TimeRange(TimeVal("8"), TimeVal(time(hour=16)))).normalized()
    assert result == expected
