from collections import namedtuple
from datetime import date, timedelta

# IMPLEMENTATION
################################################################################

Transaction = namedtuple(
    "Transaction",
    ["credit", "debit", "amount"]
)

Entry = namedtuple(
    "Entry",
    ["date", "credit", "debit", "amount", "description"]
)

Event = namedtuple(
    "Event",
    ["date", "description", "last_entry"]
)

def increment_month(d):

    """
    >>> increment_month(date(2016, 5, 4))
    datetime.date(2016, 6, 4)
    >>> increment_month(date(2016, 12, 4))
    datetime.date(2017, 1, 4)
    """

    year = d.year
    month = d.month + 1
    if month == 13:
        month = 1
        year += 1

    return date(year, month, d.day)

def earliest_day_after(d, day):

    """
    >>> earliest_day_after(date(2016, 5, 4), 3)
    datetime.date(2016, 6, 3)
    >>> earliest_day_after(date(2016, 5, 4), 4)
    datetime.date(2016, 5, 4)
    >>> earliest_day_after(date(2016, 5, 4), 5)
    datetime.date(2016, 5, 5)
    """

    if d.day > day:
        d = increment_month(d)

    return date(d.year, d.month, day)

def earliest_weekday(d):

    """
    >>> earliest_weekday(date(2016, 3, 4))
    datetime.date(2016, 3, 4)
    >>> earliest_weekday(date(2016, 3, 5))
    datetime.date(2016, 3, 4)
    >>> earliest_weekday(date(2016, 3, 6))
    datetime.date(2016, 3, 4)
    """

    if d.weekday() <= 4:
        return d

    return d - timedelta(days=d.weekday()-4)

def recurring_date_range_by_date(day, start, end):

    """
    >>> list(recurring_date_range_by_date(5, date(2016, 5, 4), date(2016, 7, 15)))
    [datetime.date(2016, 5, 5), datetime.date(2016, 6, 5), datetime.date(2016, 7, 5)]
    """

    cur = earliest_day_after(start, day)

    while cur <= end:
        yield cur
        cur = increment_month(cur)

def recurring_date_range_by_interval(interval, start, end):

    """
    >>> list(recurring_date_range_by_interval(timedelta(weeks=2), date(2016, 3, 10), date(2016, 4, 30)))
    [datetime.date(2016, 3, 10), datetime.date(2016, 3, 24), datetime.date(2016, 4, 7), datetime.date(2016, 4, 21)]
    """

    cur = start
    while cur <= end:
        yield cur
        cur = cur + interval

def earliest_weekday_date_range_by_interval(init, interval, start, end):

    """
    >>> list(earliest_weekday_date_range_by_interval(date(2016, 3, 5), timedelta(weeks=2), date(2016, 3, 10), date(2016, 4, 30)))
    [datetime.date(2016, 3, 18), datetime.date(2016, 4, 1), datetime.date(2016, 4, 15), datetime.date(2016, 4, 29)]
    """

    for d in recurring_date_range_by_interval(interval, init, end):
        actual = earliest_weekday(d)
        if actual < start:
            continue

        yield actual

def create_entry(transaction, date, description):
    return Entry(
        date,
        transaction.credit,
        transaction.debit,
        transaction.amount,
        description
    )

def create_recurring_entry_by_date(t, descr, day):

    """
    >>> t = Transaction("checking", "savings", 100)
    >>> dr = (date(2016, 5, 4), date(2016, 7, 15))
    >>> x = list(create_recurring_entry_by_date(t, "save", 5)(dr))
    >>> x[0]
    Entry(date=datetime.date(2016, 5, 5), credit='checking', debit='savings', amount=100, description='save')
    >>> len(x)
    3
    """

    def wrapper(dr):
        for d in recurring_date_range_by_date(day, *dr):
            yield create_entry(t, d, descr)

    return wrapper

def create_recurring_entry_by_interval(t, descr, start, interval):

    """
    >>> t = Transaction("", "checking", 100)
    >>> dr = (date(2016, 3, 12), date(2016, 4, 30))
    >>> start = date(2016, 3, 10)
    >>> x = list(create_recurring_entry_by_interval(t, "paycheck", start, timedelta(weeks=2))(dr))
    >>> x[0]
    Entry(date=datetime.date(2016, 3, 24), credit='', debit='checking', amount=100, description='paycheck')
    >>> len(x)
    3
    """

    def wrapper(dr):
        for d in earliest_weekday_date_range_by_interval(start, interval, *dr):
            yield create_entry(t, d, descr)

    return wrapper

def create_recurring_entry_by_interval_raw(t, descr, interval):
    def wrapper(dr):
        cur, end = dr
        while cur <= end:
            yield create_entry(t, cur, descr)
            cur += interval

    return wrapper

class Balance(object):
    def __init__(self, actions, eventers, **accounts):
        self.accounts = accounts
        self.actions = actions
        self.eventers = eventers
        self.events = []

    def process_one(self, entry):
        if entry.credit in self.accounts:
            self.accounts[entry.credit] -= entry.amount

        if entry.debit in self.accounts:
            self.accounts[entry.debit] += entry.amount

        for eventer in self.eventers:
            for event in eventer(self.accounts, entry):
                self.events.append(event)

    def process(self, entries):
        for entry in entries:
            self.process_one(entry)
            yield entry

            last_entry = entry
            for action in self.actions:
                for extra_entry in action(self.accounts, last_entry):
                    self.process_one(extra_entry)
                    yield extra_entry
                    last_entry = extra_entry

# IMPLEMENTATION
################################################################################

def create_bill(amount):
    return Transaction("checking", "", amount)

def create_income(amount):
    return Transaction("", "checking", amount)

def recur_by_day_of_month(t, descr, day):
    return create_recurring_entry_by_date(t, descr, day)

def recur_every_2_weeks(t, descr, last):
    return create_recurring_entry_by_interval(t, descr, last, timedelta(weeks=2))

def recur_every_day(t, descr):
    return create_recurring_entry_by_interval_raw(t, descr, timedelta(days=1))

def one_time_entry(t, descr, d):
    def wrapper(dr):
        if d >= dr[0] and d <= dr[1]:
            yield create_entry(t, dr[0], descr)

    return wrapper

def auto_transfer_on_income(pct, expr, description):
    def wrapper(accounts, entry):
        if entry.debit == "checking" and expr in entry.description and entry.amount > 0:
            save = (accounts.get("checking", 0) - entry.amount) * pct
            if save > 0:
                t = Transaction("checking", "savings", save)
                yield create_entry(t, entry.date, description)

    return wrapper

def auto_transfer_on_negative_balance(chunk, description):

    assert chunk > 0

    def wrapper(accounts, entry):
        if entry.credit == "checking":
            checking = accounts.get("checking", 0)
            savings = accounts.get("savings", 0)

            if checking < 0:
                attempt = chunk
                while attempt < -checking:
                    attempt += chunk

                if attempt > savings:
                    attempt = -checking

                assert attempt >= 0

                if savings >= attempt:
                    t = Transaction("savings", "checking", attempt)
                    yield create_entry(t, entry.date, description)

                else:
                    raise ValueError("{!r} would result in negative balance of {} in savings".format(
                        description, savings - attempt))

    return wrapper

def assets_go_negative_eventer(*assets):
    def wrapper(accounts, entry):
        total = sum(accounts.get(asset, 0) for asset in assets)
        if total < 0:
            yield Event(entry.date, "assets at ${:.2f}".format(total), entry)

    return wrapper

def withdraw_eventer(account):
    def wrapper(accounts, entry):
        if entry.credit == account:
            yield Event(entry.date,
                "withdraw ${:.2f} from {!r} -> {!r}".format(entry.amount,
                    entry.credit, entry.debit),
                entry)

    return wrapper
