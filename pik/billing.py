# -*- coding: utf-8
import collections
import datetime as dt
from pik.util import parse_iso8601_date

class Invoice(object):
    def __init__(self, account_id, date, lines):
        self.account_id = account_id
        self.date = date
        self.lines = lines

    def total(self):
        return sum(l.price for l in self.lines)

    def to_json(self):
        return {'account_id' : self.account_id,
                'date' : self.date.isoformat(),
                'lines' : [line.to_json() for line in self.lines]}

    @staticmethod
    def from_json(json_dict):
        return Invoice(json_dict['account_id'],
                       parse_iso8601_date(json_dict['date']),
                       [InvoiceLine.from_json(line) for line in json_dict['lines']])

    def to_csvrow(self):
        """
        Convert to CSV row that can be fed back to the system as SimpleEvents
        to act as the basis for the next billing round.

        SimpleEvent CSV format: Tapahtumapäivä,Maksajan viitenumero,Selite,Summa

        """
        return [self.date.isoformat(), self.account_id, "Lentotilin saldo " + self.date.isoformat(), self.total()]

class InvoiceLine(object):
    def __init__(self, account_id, date, item, price, rule, event):
        self.account_id = account_id # Account for which this line was generated
        self.date = date
        self.item = item
        self.price = price
        self.rule = rule # Rule that generated this invoice line
        self.event = event # Event that generated this invoice line

    def __str__(self):
        return "%s: %f <- %s" %(self.account_id, self.price, self.item)

    def to_json(self):
        return {'account_id' : self.account_id,
                'date' : self.date.isoformat(),
                'item' : self.item,
                'price' : self.price}
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
    Provides numeric variables for accounts
    """
    def __init__(self):
        self.account_contexts = collections.defaultdict(lambda: 0)

    def get(self, account_id, variable_id):
        return self.account_contexts[(account_id, variable_id)]

    def set(self, account_id, variable_id, value):
        self.account_contexts[(account_id, variable_id)] = value

    def to_json(self):
        result = collections.defaultdict(lambda: {})
        for k, v in self.account_contexts.items():
            account_id, variable_id = k
            result[account_id][variable_id] = v
        return result

    @staticmethod
    def from_json(json_dict):
        result = BillingContext()
        for account_id, account_vars in json_dict.items():
            for var_name, value in account_vars:
                result.set(account_id, var_name, value)
        return result
