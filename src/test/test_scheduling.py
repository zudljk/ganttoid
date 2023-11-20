import ganttoid.scheduling as scheduling
from datetime import datetime


def hours(n):
    return n * 60 * 60 * 1000


def test_subtract_more_hours():
    end_date = datetime(2023, 9, 10, 14, 0)
    expected = datetime(2023, 9, 4, 10, 0)
    actual = scheduling.subtract(end_date, hours(52))
    assert actual == expected


def test_subtract_no_wrap():
    end_date = datetime(2023, 6, 30, 16, 0)
    expected = datetime(2023, 6, 29, 12, 0)
    actual = scheduling.subtract(end_date, hours(12))
    assert actual == expected


def test_subtract_whole_days():
    end_date = datetime(2023, 6, 30, 16, 0)
    expected = datetime(2023, 6, 29, 8, 0)
    actual = scheduling.subtract(end_date, hours(16))
    assert actual == expected
    

def test_subtract_wrap_to_previous_day():
    end_date = datetime(2023, 9, 10, 10, 0)
    expected = datetime(2023, 9, 3, 14, 0)
    actual = scheduling.subtract(end_date, hours(52))
    assert actual == expected
