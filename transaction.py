from collections import namedtuple, defaultdict
from datetime import date, timedelta
from functools import partial
from dates import recur_once, recur_by_delta, recur_weekly, recur_monthly, \
        recur_yearly, ending, beginning

from util import OrderedStream, Buffer

Entry = namedtuple("Entry", ["date", "transaction"])

Transaction = namedtuple("Transaction",
        ["amount", "debit", "credit", "description"])


def generate_entries(recurrence, transaction):
    for d in recurrence:
        yield Entry(d, transaction)


def ledger_key(entry):
    return entry.date


class Ledger(object):
    def __init__(self,
            window=timedelta(days=30), accounts=None, actors=None, alerters=None):

        self.window = window
        self.accounts = defaultdict(float)
        if accounts:
            self.accounts.update(accounts)

        self.actors = actors or []
        self.alerters = alerters or []
        self.sources = []
        self.alerts = Buffer()
        self.t = None
        self.assets = []
        self.liabilities = []

    def add_account(self, name, value=0):
        assert name not in self.accounts
        self.accounts[name] = value

    def set_assets(self, *accounts):
        self.assets = accounts

    def set_liabilities(self, *accounts):
        self.liabilities = accounts

    def add_alerter(self, alerter):
        self.alerters.append(alerter)

    def add_actor(self, actor):
        self.actors.append(actor)

    def add_source(self, recurrence, transaction):
        self.sources.append((recurrence, transaction))

    def add_sources(self, sources):
        for s in sources:
            self.add_source(*s)

    def process(self, os, entry):
        self.t = entry.date
        self.accounts[entry.transaction.debit] += entry.transaction.amount
        self.accounts[entry.transaction.credit] -= entry.transaction.amount

        yield entry

        for alerter in self.alerters:
            event = alerter(self.accounts, entry)
            if event:
                self.alerts.add(event)

        for actor in self.actors:
            g = actor(self.accounts, entry)
            if g:
                recurrence, transaction = g
                os.add_source(generate_entries(recurrence(self.t), transaction))

    def simulate(self, start=date.today(), end=None):
        sources = [generate_entries(recurrence(start), transaction)
            for recurrence, transaction in self.sources]

        os = OrderedStream(sources, key=ledger_key)

        for entry in os.generate():
            if end and entry.date > end:
                break

            yield from self.process(os, entry)

    def get_total(self):
        assets = sum(self.accounts[a] for a in self.assets)
        liabilities = sum(self.accounts[l] for l in self.liabilities)
        return assets - liabilities


def create_recurrence(g, *args, **kwargs):

    end = kwargs.pop("end", None)
    begin = kwargs.pop("begin", None)

    def wrapper(start):
        if begin:
            if end:
                return beginning(ending(g(start, *args, **kwargs), end), begin)

            return beginning(g(start, *args, **kwargs), begin)

        if end:
            return ending(g(start, *args, **kwargs), end)

        return g(start, *args, **kwargs)

    return wrapper


interval = partial(create_recurrence, recur_by_delta)
weekly = partial(create_recurrence, recur_weekly)
monthly = partial(create_recurrence, recur_monthly)
yearly = partial(create_recurrence, recur_yearly)
once = partial(create_recurrence, recur_once)

