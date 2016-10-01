# -*- coding: utf-8
import datetime as dt
from pik.util import parse_iso8601_date

class SimpleEvent(object):
    def __init__(self, date, account_id, item, amount, ledger_account_id):
        self.date = date
        self.account_id = account_id
        self.item = item
        self.amount = amount
        self.deleted = False
        self.ledger_account_id = ledger_account_id

    def __repr__(self):
        return u"SimpleEvent(%s, %s, %s, %f, %d)" % (self.date, self.account_id, self.item, self.amount, self.ledger_account_id)

    def __unicode__(self):
        return u"SimpleEvent(%s, %s, %s, %f, %d)" % (self.date, self.account_id, self.item, self.amount, self.ledger_account_id)

    @staticmethod
    def generate_from_csv(rows):
        # CSV formats:
        # maybe with header row
        # parenthesized elements are not used
        #
        # Format 1:
        # Tapahtumapäivä,Maksajan viitenumero,Selite,Summa,(name),(invoicing year),(ledger year),ledger account id
        # 2014-03-31,114983,Pursikönttä 2014,950,Whatever,2016,2013,3740
        # ISO8601, string, string, float, (string), (int), (int), int
        #
        # Format 2: (legacy, output form previous years' invoicing)
        # Only accepted Selite is something starting with "Lentotilin saldo"
        # Tapahtumapäivä,Maksajan viitenumero,Selite,Summa,
        # 2014-03-31,114983,Pursikönttä 2014,950
        # ISO8601, string, string, float

        for row in rows:
            try:
                if row[0].startswith("Tapahtumap"):
                    # Header row
                    continue
                row = [x.decode("utf-8") for x in row]
                date = parse_iso8601_date(row[0])
                amount = float(row[3])
                if row[2].startswith("Lentotilin saldo") or row[5].startswith(u"käsin"):
                    ledger_account_id = 0
                else:
                    ledger_account_id = int(row[7])
                yield SimpleEvent(date, str(row[1]).strip(), row[2], amount, ledger_account_id)
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
                    yield SimpleEvent(txn.date, str(txn.ref), msg_template %txn.__dict__, -txn.cents/100.0, 1422)
