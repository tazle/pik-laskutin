# -*- coding: utf-8
from pik.flights import Flight
from pik.rules import FlightRule, AircraftFilter, PeriodFilter, CappedRule, AllRules, FirstRule, SetDateRule, SimpleRule, SinceDateFilter, ItemFilter, PurposeFilter, InvoicingChargeFilter, TransferTowFilter, NegationFilter
from pik.util import Period, format_invoice
from pik.billing import BillingContext, Invoice
from pik.event import SimpleEvent
from pik import nda
import datetime as dt
import csv
import sys
from collections import defaultdict
from itertools import chain
import json

if len(sys.argv) < 2:
    print "Usage: invoice-flights.py <conf-file>"
    sys.exit(1)
conf = json.load(open(sys.argv[1], 'rb'))

sources = []

for fname in conf['event_files']:
    reader = csv.reader(open(fname, 'rb'))
    sources.append(SimpleEvent.generate_from_csv(reader))

for fname in conf['flight_files']:
    reader = csv.reader(open(fname, "rb"))
    sources.append(Flight.generate_from_csv(reader))

for fname in conf['nda_files']:
    reader = nda.transactions(open(fname, 'rb'))
    # Only PIK references and incomin transactions - note that the conversion reverses the sign of the sum, since incoming money reduces the account's debt
    sources.append(SimpleEvent.generate_from_nda(reader, ["FI2413093000112458"], lambda event: event.cents > 0 and event.ref and (len(event.ref) == 4 or len(event.ref) == 6)))


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
    FirstRule([FlightRule(124, F_TOW + [PeriodFilter(Period(dt.date(2013, 4, 1), dt.date(2014, 12, 31))), TransferTowFilter()], u"Siirtohinaus, %(duration)d min"),
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
                                                     AircraftFilter("DDS", "CAO", "TOW"),
                                                     NegationFilter(TransferTowFilter())], # No kalustomaksu for transfer tows
                                                     u"Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

    # Normal simple events
    FirstRule([SetDateRule(u"pursikönttä", ctx, SimpleRule([ItemFilter(u".*[pP]ursikönttä.*")])),
               SetDateRule(u"kurssikönttä", ctx, SimpleRule([ItemFilter(u".*[kK]urssikönttä.*")])),
               SimpleRule()]),

    FlightRule(lambda flight: 2, F_KAIKKI_KONEET + F_2014 + F_LASKUTUSLISA, u"Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
]


events = sorted(chain(*sources), key=lambda event: event.date)
def events_to_lines(flights):
    for flight in flights:
        match = False
        for rule in rules:
            for line in rule.invoice(flight):
                match = True
                yield line
        if not match:
            print >> sys.stderr, flight.__repr__()


all_lines = []
by_account = defaultdict(lambda: [])
for line in events_to_lines(events):
    k = line.account_id.upper()
    if any(k.startswith(prefix) for prefix in conf['no_invoicing_prefix']):
        continue
    by_account[line.account_id].append(line)
    all_lines.append(line)

for account in sorted(by_account.keys()):
    lines = sorted(by_account[account], key=lambda line: line.date)
    invoice = Invoice(account, dt.date.today(), lines)
    print format_invoice(invoice, conf["description"])

print sum(l.price for l in all_lines)
