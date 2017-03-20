#! /usr/bin/python
# -*- coding: utf-8 -*-

import sys
import csv
from itertools import izip, repeat, count
import datetime as dt
import unicodedata
from collections import defaultdict

from hansa import SimpleHansaTransaction, SimpleHansaRow
import argparse

def mapping_reader(names, row_reader):
    for row in row_reader:
        yield {name:value.decode('utf-8') for name,value in izip(names, row)}

def gen_events(csv_fnames):
    for fname in csv_fnames:
        with open(fname, "rb") as csv_file:
            reader = csv.reader(csv_file)
            pre_header = reader.next()
            account_no = [x.decode('utf-8') for x in pre_header if x.startswith("FI")][0]
            field_names = [x.decode('utf-8') for x in reader.next()]
            for event in izip(repeat(account_no), mapping_reader(field_names, reader)):
                yield event

BANK_ACCOUNTS = {u"FI2413093000112458":1602,
                 u"FI2613093000203505":1611,
                 u"FI8118003600368090":1606,
                 u"FI1313093000207910":1612,
                 u"130930-112458":1602,
                 u"130930-203505":1611,
                 u"180036-368090":1606,
                 u"130930-207910":1612}

HANSA_ACCOUNTS = {1601:u"Käteiskassa",
                  1602:u"Merita 130930-112458 / Päätili",
                  1606:u"Suorapankki 180036-368090 / Sij.tili",
                  1611:u"Merita 130930-203505 / Kebne",
                  1612:u"Merita 130930-207910 / Vpj",
                  2112:u"Vauriorahasto",
                  6101:u"Korkotuotot",
                  6202:u"Pankkien palvelumaksut",
                  5101:u"Jäsenmaksut",
                  5103:u"Lahjoitukset",
                  1422:u"Saamiset jäseniltä",
                  }


TITLE_BY_ACCOUNT = {
    5101: lambda event: (u"Jäsenmaksu / " if _txn_sum(event) == 25 else (u"Ainaisjäsenmaksu / " if _txn_sum(event) == 250 else u"Jäsenmaksuja / "))  + (event[u"Viite"] or event[u"Saaja/Maksaja"]),
    5103: lambda event: u"Lahjoitus / " + event.get(u"Viesti", u"Ei viestiä"),
    1601: lambda event: u"Käteistilitys / " + event.get(u"Viesti", u"Ei viestiä"),
    1422: lambda event: u"Lentotilimaksu / " + event[u"Viite"],
    }

VALIDATOR_BY_ACCOUNT = {
    5101: lambda event: _txn_sum(event) == 25 or _txn_sum(event) == 250 or 'ILMAILULIITTO' in event['Saaja/Maksaja'],
    5103: lambda event: _txn_sum(event) > 0,
    1601: lambda event: _txn_sum(event) > 0,
    1422: lambda event: _txn_sum(event) > 0,
    }

class _NoTransaction(object):
    pass

NoTransaction = _NoTransaction()

def _txn_sum(event):
    return float(event[u"Määrä"].replace(",","."))

def to_txn(txn_id_gen, account, event):
    if event[u'Vienti']:
        # Already in Hansa, let's not do duplicates
        return None
    
    txn_sum = _txn_sum(event)

    hansa_bank = BANK_ACCOUNTS[account]
    year = int(event[u"Kirjauspäivä"].split('.')[-1])
    entry_date = dt.datetime.now().strftime("%d.%m.%Y")
    txn_date = event[u"Kirjauspäivä"]
    txn_ref = ""
    rows = []
    if txn_sum < 0:
        rows.append(SimpleHansaRow(hansa_bank, HANSA_ACCOUNTS[hansa_bank], credit=abs(txn_sum)))
    else:
        rows.append(SimpleHansaRow(hansa_bank, HANSA_ACCOUNTS[hansa_bank], debit=abs(txn_sum)))

    txn_title = None
    if event[u'Tapahtuma'] == 'Talletuskorko':
        txn_title = "Talletuskorko"
        if hansa_bank == 1606:
            hansa_target = 2112
        else:
            hansa_target = 6101
        if txn_sum < 0:
            raise ValueError("Negative interest")
        rows.append(SimpleHansaRow(hansa_target, HANSA_ACCOUNTS[hansa_target], credit=abs(txn_sum)))
    elif event[u'Tapahtuma'] in ('Palvelumaksu', 'Palvelumaksu ALV 0%'):
        txn_title = "Pankin palvelumaksu"
        if hansa_bank == 1606:
            hansa_target = 2112
        else:
            hansa_target = 6202
        if txn_sum > 0:
            raise ValueError("Positive banking expenses")
        rows.append(SimpleHansaRow(hansa_target, HANSA_ACCOUNTS[hansa_target], debit=abs(txn_sum)))
    elif event[u'Tapahtuma'] == 'Itsepalvelu' and event[u"Tilinumero"] in BANK_ACCOUNTS:
        if txn_sum > 0:
            raise ValueError("Should only have out account as recipient on credit entries")
        txn_title = "Oma siirto / " + event.get(u"Viesti", u"Ei viestiä")
        recipient_bank = BANK_ACCOUNTS[event[u"Tilinumero"]]
        rows.append(SimpleHansaRow(recipient_bank, HANSA_ACCOUNTS[recipient_bank], debit=abs(txn_sum)))
    elif event.get(u'Vastatili', None) is not None:
        vastatili = int(event[u'Vastatili'])
        if not VALIDATOR_BY_ACCOUNT[vastatili](event):
            raise ValueError("Invalid event: " + str(event))
        txn_title = TITLE_BY_ACCOUNT[vastatili](event)
        if txn_sum < 0:
            rows.append(SimpleHansaRow(vastatili, HANSA_ACCOUNTS[vastatili], debit=abs(txn_sum)))
        else:
            rows.append(SimpleHansaRow(vastatili, HANSA_ACCOUNTS[vastatili], credit=abs(txn_sum)))

            
    if txn_title:
        txn_id = txn_id_gen.next()
        return SimpleHansaTransaction(txn_id, year, entry_date, txn_date, txn_title, txn_ref, rows)
    else:
        return NoTransaction

def main(start_txn, csv_fnames):
    txn_id_gen = count(start_txn)
    unprocessed_count = defaultdict(lambda:0)
    for event in gen_events(csv_fnames):
        try:
            txn = to_txn(txn_id_gen, *event)
        except ValueError as e:
            print >> sys.stderr, "Error while processing", e, event
            continue

        if txn is NoTransaction:
            unprocessed_count[event[0]] += 1
            print >> sys.stderr, event[0], event[1]
            continue

        if txn is not None:
            sys.stdout.write(unicodedata.normalize("NFC", txn.hansaformat()).encode("iso-8859-1"))
    
    for act in sorted(unprocessed_count.keys()):
        print >> sys.stderr, act, unprocessed_count[act]

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage: csv2hansa.py start_number <csv file>..."
        print >> sys.stderr, "  Reads transactions from annotated Nordea text files, produces Hansa row imports"
        print >> sys.stderr, "  Hansa transactions will start from a number specified on command line. "
        print >> sys.stderr, "  Hansa acco"
        sys.exit(1)

    start_txn = int(sys.argv[1])
    csv_fnames = sys.argv[2:]
    main(start_txn, csv_fnames)
