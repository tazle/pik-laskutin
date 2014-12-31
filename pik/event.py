# -*- coding: utf-8
import datetime as dt

class SimpleEvent(object):
    def __init__(self, date, account_id, item, amount):
        self.date = date
        self.account_id = account_id
        self.item = item
        self.amount = amount
        self.deleted = False

    def __repr__(self):
        return u"SimpleEvent(%s, %s, %s, %f)" % (self.date, self.account_id, self.item, self.amount)

    @staticmethod
    def generate_from_csv(rows):
        # CSV format
        # maybe with header row
        # Tapahtumapäivä,Maksajan viitenumero,Selite,Summa
        # 2014-03-31,114983,Pursikönttä 2014,950
        # ISO8601, string, string, float
        
        for row in rows:
            row = [x.decode("utf-8") for x in row]
            try:
                float(row[3])
            except ValueError:
                continue # header row
            date = dt.date(*map(int, row[0].split("-")))
            amount = float(row[3])
            yield SimpleEvent(date, row[1], row[2], amount)

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
                    yield SimpleEvent(txn.date, txn.ref, msg_template %txn.__dict__, -txn.cents/100.0)
