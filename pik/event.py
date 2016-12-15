# -*- coding: utf-8
import datetime as dt
from pik.util import parse_iso8601_date

class SimpleEvent(object):
    def __init__(self, date, account_id, item, amount, ledger_account_id=None, ledger_year = None, rollup = False):
        self.date = date
        self.account_id = account_id
        self.item = item
        self.amount = amount
        self.deleted = False
        self.ledger_account_id = ledger_account_id # ledger_account_id is None means ledger entry is done externally
        self.ledger_year = ledger_year # ledger_year is None means ledger year is same as hansa year set in configuration
        self.rollup = rollup # indicates that this is rollup rum of previous invoicings for the account, and should not be output anywhere except onteh invoice itself

    def __repr__(self):
        return u"SimpleEvent(%s, %s, %s, %f, %s, %s)" % (self.date, self.account_id, self.item, self.amount, self.ledger_account_id, self.ledger_year)

    def __unicode__(self):
        return u"SimpleEvent(%s, %s, %s, %f, %s, %s)" % (self.date, self.account_id, self.item, self.amount, self.ledger_account_id, self.ledger_year)

    @staticmethod
    def generate_from_csv(rows):
        # CSV formats:
        # maybe with header row
        # parenthesized elements are not used
        #
        # Format 1:
        # Tapahtumapäivä,Maksajan viitenumero,Selite,Summa,(name),ledger entry,(original year),ledger account id
        # 2014-03-31,114983,Pursikönttä 2014,950,käsin,2016,2013,3740
        # ISO8601, string, string, float, string, int, (int), int
        #
        # ledger entry can be: year, in which case "ledger year" should be empty and the amount will be auto-ledgered to the year entered
        #                      "käsin", in which case corresponding entry to ledger should be made by hand, and the row is excluded from Hansa export
        #
        #
        # Format 2: (legacy, output form previous years' invoicing)
        # Only accepted Selite is something starting with "Lentotilin saldo" or "Loppusaldo 2013"
        # Tapahtumapäivä,Maksajan viitenumero,Selite,Summa,
        # 2014-03-31,114983,Pursikönttä 2014,950
        # ISO8601, string, string, float

        for row in rows:
            try:
                if row[0].startswith("Tapahtumap") or row[0].startswith("Pvm"):
                    # Header row
                    continue
                row = [x.decode("utf-8") for x in row]
                date = parse_iso8601_date(row[0])
                amount = float(row[3])
                rollup = False
                if row[2].startswith("Lentotilin saldo") or \
                   row[2].startswith("Loppusaldo 2013"):
                    rollup = True
                    ledger_account_id = None
                elif row[5].startswith(u"käsin") or len(row) < 8:
                    ledger_account_id = None
                else:
                    ledger_account_id = int(row[7])

                ledger_year = None
                if len(row) >= 7 and row[6]:
                    ledger_year = row[6]
                yield SimpleEvent(date, str(row[1]).strip(), row[2], amount, ledger_account_id, ledger_year, rollup)
            except Exception, e:
                raise ValueError("Error parsing CSV row %s" %row, e)

    @staticmethod
    def generate_from_nda(transactions, account_numbers=[], event_filter=lambda x: True, msg_template="Lentotilimaksu, %(ref)s"):
        """
        Import incoming payments from NDA file

        @param transactions pik.nda.Transaction objects
        @param account_numbers IBAN account numbers that should be imported. Only transactions whose IBAN is in this collections will be imported.
        @param event_filter Custom filter function. Only transactions that pass this filter will be imported.
        @param msg_template Message template. Template context is the dict of the transaction object.
        """
        for txn in transactions:
            if txn.iban in account_numbers:
                if event_filter(txn):
                    yield SimpleEvent(txn.date, str(txn.ref), msg_template %txn.__dict__, -txn.cents/100.0, ledger_year=txn.date.year)
