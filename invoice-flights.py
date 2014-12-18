# -*- coding: utf-8
from pik.flights import Flight
from pik.rules import FlightRule, AircraftFilter, PeriodFilter, CappedRule, AllRules, FirstRule, SetDateRule, SimpleRule, SinceDateFilter, ItemFilter, PurposeFilter, InvoicingChargeFilter
from pik.util import Period
from pik.billing import BillingContext
from pik.event import SimpleEvent
from pik import nda
import datetime as dt
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

F_2014 = [PeriodFilter(Period.full_year(2014))]
F_FK = [AircraftFilter("650")]
F_FM = [AircraftFilter("787")]
F_FQ = [AircraftFilter("733")]
F_FY = [AircraftFilter("883")]
F_DG = [AircraftFilter("952")]
F_DDS = [AircraftFilter("DDS")]
F_CAO = [AircraftFilter("CAO")]
F_TOW = [AircraftFilter("TOW")]
F_PURTSIKKA = [AircraftFilter("650","787","733","883","952")]
F_KAIKKI_KONEET = [AircraftFilter("650","787","733","883","952","DDS","TOW","CAO")]
F_PURSIK = [SinceDateFilter(ctx, u"pursikönttä")]
F_KURSSIK = [SinceDateFilter(ctx, u"kurssikönttä")]
F_LASKUTUSLISA = [InvoicingChargeFilter()]

def pursi_rule(base_filters, price, kurssi_price = 0):
    return FirstRule([FlightRule(0, base_filters + F_PURSIK, u"Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                      FlightRule(kurssi_price, base_filters + F_KURSSIK, u"Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                      FlightRule(price, base_filters)])

rules = [
    FlightRule(171, F_DDS + F_2014),
    FlightRule(134, F_CAO + F_2014),
    FlightRule(146, F_TOW + [PeriodFilter(Period(dt.date(2014, 1, 1), dt.date(2014, 3, 31)))]),
    # Variable price for TOW in the second period, based on purpose of flight
    FirstRule([FlightRule(124, F_TOW + [PeriodFilter(Period(dt.date(2013, 4, 1), dt.date(2014, 12, 31))), PurposeFilter("SII")]),
               FlightRule(104, F_TOW + [PeriodFilter(Period(dt.date(2013, 4, 1), dt.date(2014, 12, 31)))])
           ]),

    pursi_rule(F_2014 + F_FK, 15),
    pursi_rule(F_2014 + F_FM, 25, 10),
    pursi_rule(F_2014 + F_FQ, 25),
    pursi_rule(F_2014 + F_FY, 32, 17),
    pursi_rule(F_2014 + F_DG, 40),

    # Koululentomaksu
    FlightRule(lambda flight: 5, F_PURTSIKKA + F_2014 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

    CappedRule(u"kalustomaksu_total", 90, ctx,
               AllRules([CappedRule(u"kalustomaksu_pursi", 70, ctx,
                                     FlightRule(10, [PeriodFilter(Period.full_year(2014)),
                                                          AircraftFilter("650", "733", "787", "883", "952")],
                                                     u"Kalustomaksu, %(aircraft)s, %(duration)d min")),
                          CappedRule(u"kalustomaksu_moottori", 70, ctx,
                                     FlightRule(10, [PeriodFilter(Period.full_year(2014)),
                                                          AircraftFilter("DDS", "CAO", "TOW")],
                                                     u"Kalustomaksu, %(aircraft)s, %(duration)d min"))])),
    FirstRule([SetDateRule(u"pursikönttä", ctx, SimpleRule([ItemFilter(u".*[pP]ursikönttä.*")])),
               SetDateRule(u"kurssikönttä", ctx, SimpleRule([ItemFilter(u".*[kK]urssikönttä.*")])),
               SimpleRule()]),

    FlightRule(lambda flight: 2, F_KAIKKI_KONEET + F_2014 + F_LASKUTUSLISA, u"Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
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
