# -*- coding: utf-8
from pik.flights import Flight
from pik.rules import HourlyPriceRule, AircraftFilter, PeriodFilter, CappedRule, AllRules, FirstRule, SetDateRule, SimpleRule, SinceDateFilter, ItemFilter
from pik.util import Period
from pik.billing import BillingContext
from pik.event import SimpleEvent
import csv
import sys
from collections import defaultdict
from itertools import chain

sources = []
sources.append(SimpleEvent.generate_from_csv(csv.reader(sys.stdin)))
for fname in sys.argv[1:]:
    reader = csv.reader(open(fname, "rb"))
    sources.append(Flight.generate_from_csv(reader))

ctx = BillingContext()

rules = [
    HourlyPriceRule(171, [PeriodFilter(Period.full_year(2014)), AircraftFilter("DDS")]),
    FirstRule([HourlyPriceRule(0, [PeriodFilter(Period.full_year(2014)), AircraftFilter("650"), SinceDateFilter(ctx, u"pursikönttä")], u"Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
               HourlyPriceRule(0, [PeriodFilter(Period.full_year(2014)), AircraftFilter("650"), SinceDateFilter(ctx, u"kurssikönttä")], u"Lento, kurssiköntällä, %(aircraft)s, %(duration)d min"),
               HourlyPriceRule(15, [PeriodFilter(Period.full_year(2014)), AircraftFilter("650")])]),
    HourlyPriceRule(25, [PeriodFilter(Period.full_year(2014)), AircraftFilter("733")]),
    HourlyPriceRule(25, [PeriodFilter(Period.full_year(2014)), AircraftFilter("787")]),
    HourlyPriceRule(32, [PeriodFilter(Period.full_year(2014)), AircraftFilter("883")]),
    HourlyPriceRule(40, [PeriodFilter(Period.full_year(2014)), AircraftFilter("952")]),

    CappedRule(u"kalustomaksu_total", 90, ctx,
               AllRules([CappedRule(u"kalustomaksu_pursi", 70, ctx,
                                     HourlyPriceRule(10, [PeriodFilter(Period.full_year(2014)),
                                                          AircraftFilter("650", "733", "787", "883", "952")],
                                                     u"Kalustomaksu, %(aircraft)s, %(duration)d min")),
                          CappedRule(u"kalustomaksu_moottori", 70, ctx,
                                     HourlyPriceRule(10, [PeriodFilter(Period.full_year(2014)),
                                                          AircraftFilter("DDS", "CAO", "TOW")],
                                                     u"Kalustomaksu, %(aircraft)s, %(duration)d min"))])),
    FirstRule([SetDateRule(u"pursikönttä", ctx, SimpleRule([ItemFilter(u".*[pP]ursikönttä.*")])),
               SetDateRule(u"kurssikönttä", ctx, SimpleRule([ItemFilter(u".*[kK]urssikönttä.*")])),
               SimpleRule()])
]


events = chain(*sources)
def events_to_lines(flights):
    for flight in flights:
        for rule in rules:
            for line in rule.invoice(flight):
                yield line


all_lines = []
by_account = defaultdict(lambda: [])
for line in events_to_lines(events):
    by_account[line.account_id].append(line)
    all_lines.append(line)

for account in sorted(by_account.keys()):
    lines = by_account[account]
    print account, sum(l.price for l in lines)
    for l in lines:
        print u"  " + l.item

print sum(l.price for l in all_lines)
