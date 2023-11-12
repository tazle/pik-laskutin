# -*- coding: utf-8
import collections
import datetime as dt
from pik.util import parse_iso8601_date
import decimal

class Invoice(object):
    def __init__(self, account_id, date, lines):
        self.account_id = account_id
        self.date = date
        self.lines = lines

    def total(self):
        with decimal.localcontext() as ctx:
            return sum(l.price for l in self.lines).quantize(decimal.Decimal('.01'))

    def to_json(self):
        return {'account_id' : self.account_id,
                'date' : self.date.isoformat(),
                'lines' : [line.to_json() for line in self.lines]}

    @staticmethod
    def from_json(json_dict):
        return Invoice(json_dict['account_id'],
                       parse_iso8601_date(json_dict['date']),
                       [InvoiceLine.from_json(line) for line in json_dict['lines']])

    def to_csvrow_total(self):
        """
        Convert to CSV row that can be fed back to the system as SimpleEvents
        to act as the basis for the next billing round.

        SimpleEvent CSV format: Tapahtumapäivä,Maksajan viitenumero,Selite,Summa

        """
        return [self.date.isoformat(), self.account_id, "Lentotilin saldo " + self.date.isoformat(), self.total()]

    def to_csvrows(self):
        """
        Convert to CSV rows that can be used in bookkeeping.

        CSV format: Tapahtumapäivä,Laskutuspäivä,Maksajan viitenumero,Selite,Summa

        """
        result = []
        for line in self.lines:
            result.append(line.to_csvrow())
        return result

class InvoiceLine(object):
    CsvRow = collections.namedtuple('InvoiceLineCsvRow', ['date', 'account_id', 'item', 'price', 'ledger_year'])
    def __init__(self, account_id, date, item, price, rule, event, ledger_account_id, ledger_year=None, rollup=False):
        self.account_id = account_id # Account for which this line was generated
        self.date = date
        self.item = item
        self.price = price if isinstance(price, decimal.Decimal) else decimal.Decimal(price).quantize(decimal.Decimal('.01'))
        self.rule = rule # Rule that generated this invoice line
        self.event = event # Event that generated this invoice line
        self.ledger_account_id = ledger_account_id # Ledger account for this event, e.g. "income from past years"
        self.ledger_year = ledger_year # Ledger year for this event
        self.rollup = rollup

    def __str__(self):
        return "%s: %f <- %s" %(self.account_id, self.price, self.item)

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return "%s: %f <- %s" %(self.account_id, self.price, self.item)

    def to_csvrow(self):
        """
        Convert to CSV row that can be used in bookkeeping.

        CSV format: Tapahtumapäivä,Laskutuspäivä,Maksajan viitenumero,Selite,Summa,Kirjanpitovuosi

        """
        return InvoiceLine.CsvRow(self.date.isoformat(), self.account_id, self.item, self.price, self.ledger_year)

    def to_json(self):
        return {'account_id' : self.account_id,
                'date' : self.date.isoformat(),
                'item' : self.item,
                'price' : self.price,
                'ledger_account_id' : self.ledger_account_id}
               # How to encode rules and events? Need dispatch to actual objects
               # Also, rules are stateful
               #'rule' : self.rule.to_json(),
               #'event' : self.event.to_json()}

    @staticmethod
    def from_json(json_dict):
        return InvoiceLine(json_dict['account_id'],
                           parse_iso8601_date(json_dict['date']),
                           json_dict['item'],
                           json_dict['price'],
                           None,
                           None)


class BillingContext(object):
    """
    Provides numeric and string variables for accounts
    """
    def __init__(self):
        self.account_contexts = collections.defaultdict(lambda: 0)

    def get(self, account_id, variable_id):
        return self.account_contexts[(account_id, variable_id)]

    def set(self, account_id, variable_id, value):
        self.account_contexts[(account_id, variable_id)] = value

    def to_json(self):
        result = collections.defaultdict(lambda: {})
        for k, v in list(self.account_contexts.items()):
            account_id, variable_id = k
            result[account_id][variable_id] = v
        return result

    @staticmethod
    def from_json(json_dict):
        result = BillingContext()
        for account_id, account_vars in list(json_dict.items()):
            for var_name, value in list(account_vars.items()):
                result.set(account_id, var_name, value)
        return result
