# -*- coding: utf-8
import datetime as dt

class SimpleEvent(object):
    def __init__(self, date, account_id, item, amount):
        self.date = date
        self.account_id = account_id
        self.item = item
        self.amount = amount
        self.deleted = False

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
