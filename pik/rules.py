# -*- coding: utf-8

# All rules must have:
#
# "invoice" method, which takes: a source event, and produces a list of pik.billing.InvoiceLine objects

from pik.event import SimpleEvent
from pik.flights import Flight
from pik.billing import InvoiceLine
import datetime as dt
import re
import numbers

class SimpleRule(object):
    def __init__(self, filters=[]):
        self.filters = filters

    def invoice(self, event):
        if isinstance(event, SimpleEvent):
            if all(f(event) for f in self.filters):
                return [InvoiceLine(event.account_id, event.date, event.item, event.amount, self, event)]
            
        return []

class SinceDateFilter(object):
    def __init__(self, ctx, variable_id):
        self.ctx = ctx
        self.variable_id = variable_id

    def __call__(self, event):
        try:
            val = self.ctx.get(event.account_id, self.variable_id)
            limit = dt.date(*map(int, val.split("-")))
            return limit <= event.date
        except Exception:
            return False
                

class ItemFilter(object):
    def __init__(self, regex):
        self.regex = regex

    def __call__(self, event):
        return re.search(self.regex, event.item)

class PeriodFilter(object):
    def __init__(self, period):
        self.period = period

    def __call__(self, event):
        return event.date in self.period

class AircraftFilter(object):
    def __init__(self, *aircraft):
        self.aircraft = aircraft

    def __call__(self, event):
        return event.aircraft in self.aircraft

class PurposeFilter(object):
    def __init__(self, *purposes):
        self.purposes = purposes

    def __call__(self, event):
        return event.purpose in self.purposes

class TransferTowFilter(object):
    def __call__(self, event):
        return bool(event.transfer_tow)

class InvoicingChargeFilter(object):
    def __call__(self, event):
        return bool(event.invoicing_comment)

class FlightRule(object):
    def __init__(self, price, filters=[], template="Lento, %(aircraft)s, %(duration)d min"):
        """
        @param price Hourly price, in euros, or pricing function that takes Flight event as parameter and returns price
        @param filters Input filters (such as per-aircraft)
        @param template Description tmeplate. Filled using string formatting with the event object's __dict__ context
        """
        if isinstance(price, numbers.Number):
            self.pricing = lambda event: event.duration * (price / 60.0)
        else:
            self.pricing = price
        self.filters = filters
        self.template = template

    def invoice(self, event):
        if isinstance(event, Flight):
            if all(f(event) for f in self.filters):
                line = self.template %event.__dict__
                price = self.pricing(event)
                return [InvoiceLine(event.account_id, event.date, line, price, self, event)]
            
        return []

class AllRules(object):
    def __init__(self, inner_rules):
        """
        @param inner_rules Apply all inner rules to the incoming event and gather their InvoiceLines into the output
        """
        self.inner_rules = inner_rules

    def invoice(self, event):
        result = []
        for rule in self.inner_rules:
            result.extend(rule.invoice(event))
        return result

class FirstRule(object):
    def __init__(self, inner_rules):
        """
        @param inner_rules Apply inner rules in order, return with lines from first rule that produces output
        """
        self.inner_rules = inner_rules

    def invoice(self, event):
        for rule in self.inner_rules:
            lines = rule.invoice(event)
            if lines:
                return lines
        return []

class CappedRule(object):
    def __init__(self, variable_id, cap_price, context, inner_rule):
        """
        @param variable_id Variable to use for capping
        @param inner_rule Rule that produces InvoiceLines that this object filters
        @param cap_price Hourly price, in euros
        @param context Billing context in which to store cap data
        """
        self.variable_id = variable_id
        self.inner_rule = inner_rule
        self.cap_price = cap_price
        self.context = context

    def invoice(self, event):
        lines = self.inner_rule.invoice(event)
        return list(self._filter_lines(lines))
    
    def _filter_lines(self, lines):
        for line in lines:
            ctx_val = self.context.get(line.account_id, self.variable_id)
            if ctx_val >= self.cap_price:
                # Already over cap, filter lines out
                continue
            if ctx_val + line.price > self.cap_price:
                # Cap price of line to match cap
                line = InvoiceLine(line.account_id, line.date, line.item + ", rajattu", self.cap_price - ctx_val, self, line.event)
            self.context.set(line.account_id, self.variable_id, ctx_val + line.price)
            yield line

class SetDateRule(object):
    def __init__(self, variable_id, context, inner_rule):
        """
        Rule that sets a variable to date of last line produced by inner rule
        """
        self.variable_id = variable_id
        self.inner_rule = inner_rule
        self.context = context

    def invoice(self, event):
        lines = self.inner_rule.invoice(event)
        for line in lines:
            self.context.set(line.account_id, self.variable_id, line.date.isoformat())
        return lines
