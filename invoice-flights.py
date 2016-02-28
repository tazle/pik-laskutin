# -*- coding: utf-8
from pik.flights import Flight
from pik.rules import FlightRule, AircraftFilter, PeriodFilter, CappedRule, AllRules, FirstRule, SetDateRule, SimpleRule, SinceDateFilter, ItemFilter, PurposeFilter, InvoicingChargeFilter, TransferTowFilter, NegationFilter
from pik.util import Period, format_invoice, parse_iso8601_date
from pik.billing import BillingContext, Invoice
from pik.event import SimpleEvent
from pik import nda
import datetime as dt
import csv
import sys
from collections import defaultdict
from itertools import chain
import json
import os


def make_rules(ctx=BillingContext()):
    ID_KM_2014 = u"kausimaksu_tot_2014"
    ID_KM_P_2014 = u"kausimaksu_pursi_2014"
    ID_KM_M_2014 = u"kausimaksu_motti_2014"

    ID_KM_2015 = u"kausimaksu_tot_2015"
    ID_KM_P_2015 = u"kausimaksu_pursi_2015"
    ID_KM_M_2015 = u"kausimaksu_motti_2015"

    ID_PK_2014 = u"pursikönttä_2014"
    ID_PK_2015 = u"pursikönttä_2015"

    ID_KK_2014 = u"kurssikönttä_2014"
    ID_KK_2015 = u"kurssikönttä_2015"


    F_2014 = [PeriodFilter(Period.full_year(2014))]
    F_FK = [AircraftFilter("650")]
    F_FM = [AircraftFilter("787")]
    F_FQ = [AircraftFilter("733")]
    F_FY = [AircraftFilter("883")]
    F_DG = [AircraftFilter("952")]
    F_TK = [AircraftFilter("TK")]
    F_DDS = [AircraftFilter("DDS")]
    F_CAO = [AircraftFilter("CAO")]
    F_TOW = [AircraftFilter("TOW")]
    F_MOTTI = [AircraftFilter("DDS","CAO","TOW")]
    F_PURTSIKKA = [AircraftFilter("650","787","733","883","952")]
    F_KAIKKI_KONEET = F_MOTTI + F_PURTSIKKA
    F_PURSIK = [SinceDateFilter(ctx, ID_PK_2014)]
    F_KURSSIK = [SinceDateFilter(ctx, ID_KK_2014)]
    F_LASKUTUSLISA = [InvoicingChargeFilter()]

    F_2015 = [PeriodFilter(Period.full_year(2015))]
    F_PURTSIKKA_2015 = [AircraftFilter("650","787","733","883","952","TK")]
    F_KAIKKI_KONEET_2015 = F_MOTTI + F_PURTSIKKA_2015
    F_PURSIK_2015 = [SinceDateFilter(ctx, ID_PK_2015)]
    F_KURSSIK_2015 = [SinceDateFilter(ctx, ID_KK_2015)]

    F_2016 = [PeriodFilter(Period.full_year(2016))]


    def pursi_rule(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, base_filters + F_PURSIK, u"Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, base_filters + F_KURSSIK, u"Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, base_filters)])

    rules_2014 = [
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

        CappedRule(ID_KM_2014, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2014, 70, ctx,
                                         FlightRule(10, [PeriodFilter(Period.full_year(2014)),
                                                              AircraftFilter("650", "733", "787", "883", "952")],
                                                         u"Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2014, 70, ctx,
                                         FlightRule(10, [PeriodFilter(Period.full_year(2014)),
                                                         AircraftFilter("DDS", "CAO", "TOW"),
                                                         NegationFilter(TransferTowFilter())], # No kalustomaksu for transfer tows
                                                         u"Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2014, ctx, SimpleRule([ItemFilter(u".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2014, ctx, SimpleRule([ItemFilter(u".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2014)]),

        FlightRule(lambda flight: 2, F_KAIKKI_KONEET + F_2014 + F_LASKUTUSLISA, u"Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]

    rules_2015 = [
        FlightRule(171, F_DDS + F_2015),
        # Variable price for TOW in the second period, based on purpose of flight
        FirstRule([FlightRule(124, F_TOW + F_2015 + [TransferTowFilter()], u"Siirtohinaus, %(duration)d min"),
                   FlightRule(104, F_TOW + F_2015)
               ]),

        pursi_rule(F_2015 + F_FK, 15),
        pursi_rule(F_2015 + F_FM, 25, 10),
        pursi_rule(F_2015 + F_FQ, 25),
        pursi_rule(F_2015 + F_FY, 32, 32, 10),
        pursi_rule(F_2015 + F_DG, 40, 10, 10),
        pursi_rule(F_2015 + F_TK, 25, 10, 0),

        # Koululentomaksu
        FlightRule(lambda flight: 5, F_PURTSIKKA + F_2015 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2015, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2015, 70, ctx,
                                         FlightRule(10, F_2015 + F_PURTSIKKA_2015,
                                                         u"Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2015, 70, ctx,
                                         FlightRule(10, F_2015 + F_MOTTI,
                                                         u"Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(u"pursikönttä_2015", ctx, SimpleRule([ItemFilter(u".*[pP]ursikönttä.*")])),
                   SetDateRule(u"kurssikönttä_2015", ctx, SimpleRule([ItemFilter(u".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2015)]),

        FlightRule(lambda flight: 2, F_KAIKKI_KONEET + F_2015 + F_LASKUTUSLISA, u"Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]

    return rules_2014 + rules_2015



def events_to_lines(events, rules):
    for event in events:
        match = False
        for rule in rules:
            for line in rule.invoice(event):
                match = True
                yield line
        if not match:
            print >> sys.stderr, "No match for event", event.__repr__()

def grouped_lines(lines):
    by_account = defaultdict(lambda: [])
    for line in lines:
        k = line.account_id.upper()
        if any(k.startswith(prefix) for prefix in conf['no_invoicing_prefix']):
            continue
        by_account[line.account_id].append(line)
    return by_account

def events_to_invoices(events, rules, invoice_date=dt.date.today()):
    by_account = grouped_lines(events_to_lines(events, rues))
    for account in sorted(by_account.keys()):
        lines = sorted(by_account[account], key=lambda line: line.date)
        yield Invoice(account, invoice_date, lines)


def write_invoices_to_files(invoices, conf):
    for invoice in invoices:
        account = invoice.account_id
        with open(os.path.join(conf["out_dir"], account + ".txt"), "wb") as f:
            f.write(format_invoice(invoice, conf["description"]).encode("utf-8"))

def write_total_csv(invoices, fname):
    import csv
    writer = csv.writer(open(fname, 'wb'))
    writer.writerows(invoice.to_csvrow() for invoice in invoices)

def is_invoice_small_sum(invoice):
    return abs(invoice.total()) <= 0.01

def make_account_validator(valid_accounts):
    def is_invoice_account_valid(invoice):
        return invoice.account_id in valid_accounts
    return is_invoice_account_valid

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: invoice-flights.py <conf-file> <total-csv-file>"
        sys.exit(1)
    conf = json.load(open(sys.argv[1], 'rb'))
    total_csv_fname = sys.argv[2]

    sources = []

    ctx = BillingContext()
    if "context_file_in" in conf:
        context_file = conf["context_file_in"]
        if os.path.isfile(context_file):
            ctx = BillingContext.from_json(json.load(open(context_file, "r")))
    rules = make_rules(ctx)

    for fname in conf['event_files']:
        reader = csv.reader(open(fname, 'rb'))
        sources.append(SimpleEvent.generate_from_csv(reader))

    for fname in conf['flight_files']:
        reader = csv.reader(open(fname, "rb"))
        sources.append(Flight.generate_from_csv(reader))

    for fname in conf['nda_files']:
        bank_txn_date_filter = lambda: True
        if 'bank_txn_dates' in conf:
            dates = map(parse_iso8601_date, conf['bank_txn_dates'])
            bank_txn_date_filter = PeriodFilter(Period(*dates))

        reader = nda.transactions(open(fname, 'rb'))
        # Only PIK references and incoming transactions - note that the conversion reverses the sign of the sum, since incoming money reduces the account's debt
        sources.append(SimpleEvent.generate_from_nda(reader, ["FI2413093000112458"], lambda event: event.cents > 0 and event.ref and (len(event.ref) == 4 or len(event.ref) == 6)))

    invoice_date = parse_iso8601_date(conf['invoice_date'])
    events = sorted(chain(*sources), key=lambda event: event.date)

    invoices = list(events_to_invoices(events, rules, invoice_date=invoice_date))

    if "context_file_out" in conf:
        json.dump(ctx.to_json(), open(conf["context_file_out"], "w"))

    is_account_valid = make_account_validator(conf["valid_accounts"])

    def is_valid_invoice(invoice):
        return not is_invoice_small_sum(invoice) and is_account_valid(invoice)

    valid_invoices = [i for i in invoices if is_valid_invoice(i)]
    invalid_invoices = [i for i in invoices if not is_valid_invoice(i)]

    write_invoices_to_files(valid_invoices, conf)
    write_total_csv(valid_invoices, total_csv_fname)

    machine_readable_invoices = [invoice.to_json() for invoice in invoices]

    print json.dumps(machine_readable_invoices)

    invalid_account = []
    invalid_sum = []
    for invoice in invalid_invoices:
        if not is_account_valid(invoice):
            invalid_account.append(invoice)
            print >> sys.stderr, "Invalid account:", invoice.account_id
        elif is_invoice_small_sum(invoice):
            if invoice.total() != 0:
                invalid_sum.append(invoice)
                print >> sys.stderr, "Invoice with small sum for", invoice.account_id
            else:
                print >> sys.stderr, "Invoice with zero sum for", invoice.account_id
        else:
            print >> sys.stderr, "Otherwise invalid invoice for account:", invoice.account_id

    print >> sys.stderr, "Difference, valid invoices, total", sum(i.total() for i in valid_invoices)
    print >> sys.stderr, "Owed to club, valid invoices, total", sum(i.total() for i in valid_invoices if i.total() > 0)

    print >> sys.stderr, "Owed by invalid accounts, total ", sum(i.total() for i in invalid_account if i.total() > 0)
    print >> sys.stderr, "Owed to invalid accounts, total", sum(i.total() for i in invalid_account if i.total() < 0)

    print >> sys.stderr, "Owed to club in invoices with invalid sum", sum(i.total() for i in invalid_sum if i.total() > 0)
    print >> sys.stderr, "Owed by club in invoices with invalid sum", sum(i.total() for i in invalid_sum if i.total() < 0)

