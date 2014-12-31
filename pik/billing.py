# -*- coding: utf-8
import collections

class Invoice(object):
    def __init__(self, account_id, date, lines):
        self.account_id = account_id
        self.date = date
        self.lines = lines

    def total(self):
        return sum(l.price for l in self.lines)

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
        
