from iit.core.workweek import get_workweek
from iit.types import TimeSpan
from datetime import time

def test_get_workweek():
    config = {
        "scheduling": {
            "work_week": [
                ("mon-f", "8AM - 11 a, 1PM - 7:00PM"),
                ("sat", "10AM - 4PM"),
            ]
        }
    }
    ww = get_workweek(config)
    assert len(ww) == 7
    assert not ww.sunday
    ts1 = TimeSpan(time(8, 0), time(11, 0))
    ts2 = TimeSpan(time(13, 0), time(19, 0))
    monday_expected = [ts1, ts2]
    assert ([ww.monday[i] == monday_expected[i]] for i in range(0, len(monday_expected)))

    ts1 = TimeSpan(time(10, 0), time(16, 0))
    wed_expected = [ts1,]
    assert ([ww.wednesday[i] == monday_expected[i]] for i in range(0, len(wed_expected)))