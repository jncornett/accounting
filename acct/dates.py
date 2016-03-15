from datetime import date, timedelta


def _get_next_year_month(year, month):

    """
    >>> _get_next_year_month(2012, 3)
    (2012, 4)
    >>> _get_next_year_month(2013, 12)
    (2014, 1)
    """

    month += 1
    if month > 12:
        year += 1
        month = 1

    return year, month


def _get_next_month_with_day(d, day_of_month):

    """
    >>> _get_next_month_with_day(date(2014, 2, 1), 10)
    datetime.date(2014, 2, 10)
    >>> _get_next_month_with_day(date(2014, 2, 1), 30)
    datetime.date(2014, 3, 30)
    >>> _get_next_month_with_day(date(2020, 2, 1), 29)
    datetime.date(2020, 2, 29)
    """

    assert day_of_month <= 31

    year = d.year
    month = d.month

    if day_of_month < d.day:
        year, month = _get_next_year_month(year, month)

    while True:
        try:
            return date(year, month, day_of_month)
        except ValueError:
            year, month = _get_next_year_month(year, month)


def _advance_month(d):

    """
    >>> _advance_month(date(2014, 2, 1))
    datetime.date(2014, 3, 1)
    >>> _advance_month(date(2014, 1, 29))
    datetime.date(2014, 3, 29)
    """

    year, month = _get_next_year_month(d.year, d.month)
    while True:
        try:
            return date(year, month, d.day)
        except ValueError:
            year, month = _get_next_year_month(year, month)


def _earliest_day_of_week_after(d, day_of_week):

    """
    >>> _earliest_day_of_week_after(date(2016, 3, 11), 0)
    datetime.date(2016, 3, 14)
    """

    assert 0 <= day_of_week < 7
    offset = (day_of_week - d.weekday()) % 7
    return d + timedelta(days=offset)


def _earliest_weekday_before(d):

    """
    >>> _earliest_weekday_before(date(2016, 3, 11))
    datetime.date(2016, 3, 11)
    >>> _earliest_weekday_before(date(2016, 3, 13))
    datetime.date(2016, 3, 11)
    """

    if d.weekday() < 5:
        return d

    return d - timedelta(days=d.weekday()-4)


def recur_by_delta(start, delta, initial=None):

    """
    >>> x = recur_by_delta(date(2016, 3, 12), timedelta(days=7), date(2016, 3, 13))
    >>> next(x)
    datetime.date(2016, 3, 13)
    >>> next(x)
    datetime.date(2016, 3, 20)
    >>> next(x)
    datetime.date(2016, 3, 27)
    >>> next(x)
    datetime.date(2016, 4, 3)
    """

    if initial:
        while initial < start:
            initial += delta

    else:
        initial = start

    while True:
        yield initial
        initial += delta


def recur_weekly(start, day_of_week):

    """
    >>> x = recur_weekly(date(2016, 3, 7), 4)
    >>> next(x)
    datetime.date(2016, 3, 11)
    >>> next(x)
    datetime.date(2016, 3, 18)
    >>> x = recur_weekly(date(2016, 3, 9), 0)
    >>> next(x)
    datetime.date(2016, 3, 14)
    """

    initial = _earliest_day_of_week_after(start, day_of_week)
    return recur_by_delta(start, timedelta(days=7), initial)


def recur_monthly(start, day_of_month):

    """
    >>> x = recur_monthly(date(2016, 3, 10), 14)
    >>> next(x)
    datetime.date(2016, 3, 14)
    >>> next(x)
    datetime.date(2016, 4, 14)
    >>> x = recur_monthly(date(2016, 3, 10), 2)
    >>> next(x)
    datetime.date(2016, 4, 2)
    >>> x = recur_monthly(date(2016, 4, 10), 31)
    >>> next(x)
    datetime.date(2016, 5, 31)
    >>> next(x)
    datetime.date(2016, 7, 31)
    """

    assert day_of_month <= 31

    cur = _get_next_month_with_day(start, day_of_month)

    while True:
        yield cur
        cur = _advance_month(cur)


def recur_once(start, d):

    """
    >>> x = recur_once(date(2016, 3, 12), date(2016, 3, 12))
    >>> next(x)
    datetime.date(2016, 3, 12)
    >>> x = recur_once(date(2016, 3, 10), date(2016, 3, 12))
    >>> next(x)
    datetime.date(2016, 3, 12)
    >>> x = recur_once(date(2016, 3, 10), date(2016, 3, 4))
    >>> next(x, None)
    """

    if d >= start:
        yield d


def recur_yearly(start, month, day):
    d = date(start.year, month, day)
    if d < start:
        d = date(start.year + 1, month, day)

    while True:
        yield d
        d = date(d.year, month, day)


def ending(it, end):

    """
    >>> x = iter([date(2016, 1, 1), date(2016, 2, 1), date(2016, 3, 1)])
    >>> list(ending(x, date(2016, 2, 1)))
    [datetime.date(2016, 1, 1), datetime.date(2016, 2, 1)]
    """

    for d in it:
        if d > end:
            break

        yield d


def beginning(it, begin):

    """
    >>> x = iter([date(2016, 1, 1), date(2016, 2, 1), date(2016, 3, 1)])
    >>> list(beginning(x, date(2016, 2, 1)))
    [datetime.date(2016, 2, 1), datetime.date(2016, 3, 1)]
    """

    for d in it:
        if d >= begin:
            yield d
