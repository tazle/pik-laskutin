# -*- coding: utf-8 -*-
import datetime as dt

def findrecord(records, maintype, subtype):
    for record in records:
        if record.type == maintype and record.subtype == subtype:
            return record
    return None

def ordify(d):
    result = {}
    for k,v in d.items():
        result[ord(k)] = ord(v)
    return result

debanktable = ordify({'[':'Ä', '\\':'Ö', ']':'Å',
                    '{':'ä', '|':'ö'})


def debank(str):
    # u = str.decode('latin-1')
    return str.translate(debanktable)

class Transaction(object):
    def __init__(self, metarecord, mainrecord, extrarecords=[], receipt_txns=[]):
        self.id = mainrecord.id

        self.iban = metarecord.iban
        self.bic = metarecord.bic
        self.date = mainrecord.date
        self.ledger_date = mainrecord.ledger_date
        self.value_date = mainrecord.value_date
        self.payment_date = mainrecord.payment_date

        self.name = mainrecord.name
        self.cents = mainrecord.cents
        self.metarecord = metarecord
        self.mainrecord = mainrecord
        self.extrarecords = extrarecords

        self.receipt = mainrecord.receipt
        self.is_receipt = mainrecord.is_receipt

        self.receipt_txns = receipt_txns


        if mainrecord.ref:
            self.ref = mainrecord.ref
        else:
            refrecord = findrecord(extrarecords, '11', '06')
            if refrecord:
                self.ref = refrecord.ref
            else:
                self.ref = None
        msgrecord = findrecord(extrarecords, '11', '00')
        if msgrecord:
            self.msg = msgrecord.msg
        else:
            self.msg = None

        ourrefrecord = findrecord(extrarecords, '11', '11')
        if ourrefrecord:
            self.ourref = ourrefrecord.ourref
        else:
            self.ourref = None

        recipientrecord = findrecord(extrarecords, '11', '11')
        if recipientrecord:
            self.recipient_iban = recipientrecord.recipient_iban
            self.recipient_bic = recipientrecord.recipient_bic
        else:
            self.recipient_iban = None
            self.recipient_bic = None

        self.operation = mainrecord.operation

    def __str__(self):
        return self.mainrecord.str

class Record00(object):
    def __init__(self, str):
        self.type = '00'
        self.str = str

    @property
    def iban(self):
        return self.str[1+2+3+3+14+3+12+10+17+6+19+6+3+30+18+35+40+40+30:].strip().split()[0]

    @property
    def bic(self):
        return self.str[1+2+3+3+14+3+12+10+17+6+19+6+3+30+18+35+40+40+30:].strip().split()[1]

    def __str__(self):
        return self.str.strip()

class Record10(object):
    """
    New transaction

    e.g.
T101880000311305272588WWNU02851305271305271305272720Itsepalvelu                        -000000000000044625 AJeppesen GbmH                      A                                            
T10188000001130506258883E248871305061305061305062730Palvelumaksu                       -000000000000000982EJNORDEA PANKKI SUOMI OYJ            J                                            
    """
    def __init__(self, str):
        self.type = '10'
        self.str = str


    @property
    def id(self):
        datestr = self.str[12:12+18]

    @property
    def date(self):
        return self.ledger_date

    @property
    def ledger_date(self):
        datestr = self.str[1+2+3+6+18:1+2+3+6+18+6]
        if datestr == "000000":
            return None
        else:
            return dt.datetime.strptime(datestr, "%y%m%d").date()

    @property
    def value_date(self):
        datestr = self.str[1+2+3+6+30:1+2+3+6+30+6]
        if datestr == "000000":
            return None
        else:
            return dt.datetime.strptime(datestr, "%y%m%d").date()

    @property
    def payment_date(self):
        datestr = self.str[1+2+3+6+24:1+2+3+6+24+6]
        if datestr == "000000":
            return None
        else:
            return dt.datetime.strptime(datestr, "%y%m%d").date()

    @property
    def name(self):
        return debank(self.str[108:108+35]).rstrip(' ')

    @property
    def receipt(self):
        return self.str[106].strip()

    @property
    def is_receipt(self):
        # TODO Doesn't distinguish between receipt levels
        return bool(self.str[187].strip())

    @property
    def operation(self):
        return debank(self.str[52:52+35]).rstrip(' ')

    @property
    def cents(self):
        sign = self.str[87:88]
        num = self.str[88:88+18]
        return int(sign + num.lstrip('0'))

    @property
    def euros(self):
        return float("%.2f" % (self.cents()/100.0))

    @property
    def ref(self):
        ref = self.str[159:159+20].lstrip(' ')
        if ref:
            return ref.lstrip('0')
        else:
            return None

    def __str__(self):
        return self.str.strip()

class Record11(object):
    """
    Additional information for a transaction?

    e.g. 
T1104300invoice 420098923                  
T1132311                                   DE35505700180332170000             DEUTDEFF505                                                                                                                                                                                                                                          
T110780600000300086161284007                                                  
T110780670160263718201000455                                                  

    It seems that T1132311 is receiver account in some format, T1104300 is a free-form message and T1107806 is a defined-format refrence number
    """
    def __init__(self, str):
        self.type = '11'
        self.subtype = str[6:8]
        self.str = str

        if self.subtype == '06':
            self.ref = str[8:8+35].rstrip(' \r\n').lstrip('0')
        elif self.subtype == '00':
            self.msg = debank(str[8:].rstrip(' \r\n'))
        elif self.subtype == '11':
            self.ourref = debank(str[8:8+35].rstrip(' \r\n'))
            self.recipient_iban = debank(str[8+35:8+35+35].rstrip(' \r\n'))
            self.recipient_bic = debank(str[8+70:8+70+35].rstrip(' \r\n'))

    def __repr__(self):
        return "Record11(%s, %s, %s)" %(self.type, self.subtype, self.str.strip())

    def __str__(self):
        return self.str.strip()

def check_txn_ids(txn_buf):
    return len(set(txn.id for txn in txn_buf)) == 1

def complex_txn(txn_buf):
    # Build complex transaction out of buffer, the head of which is the main transaction and the rest are parts of its receipt
    check_txn_ids(txn_buf)
    main_txn = txn_buf[0]
    return Transaction(main_txn.metarecord, main_txn.mainrecord, main_txn.extrarecords, txn_buf[1:])

def transactions(lines):
    txn_buf = []
    for txn in simple_transactions(lines):
        if not txn_buf and not txn.receipt and not txn.is_receipt:
            # Normal transaction and empty buffer
            yield txn
        elif txn_buf and not txn.is_receipt:
            # First non-receipt transaction after transaction
            # First yield buffered complex transaction, then the transaction that indicated its end
            yield complex_txn(txn_buf)
            txn_buf = []
            yield txn
        elif txn.receipt == 'E':
            # This transaction is followed by receipt transactions
            if txn_buf:
                yield complex_txn(txn_buf)
                txn_buf = []
            txn_buf.append(txn)
        elif txn_buf and txn.is_receipt:
            txn_buf.append(txn)
        else:
            raise Exception("Unexpected case", txn_buf, str(txn))

    if txn_buf:
        # End of stream, yield anything that's in the buffer
        yield complex_txn(txn_buf)

def simple_transactions(lines):
    ctx = None
    buf = []
    for l in lines:
        if l.startswith('T00'):
            ctx = Record00(l)
            continue
        if not buf:
            if l.startswith('T10'):
                r = Record10(l)
                buf.append(r)
        elif buf:
            if l.startswith('T10'):
                yield Transaction(ctx, buf[0], buf[1:])
                buf = []
                r = Record10(l)
                buf.append(r)
            elif l.startswith('T11'):
                r = Record11(l)
                buf.append(r)
            else:
                yield Transaction(ctx, buf[0], buf[1:])
                buf = []
    if buf:
        yield Transaction(ctx, buf[0], buf[1:])

if __name__ == '__main__':
    import csv
    import sys

    if 'raw' in sys.argv:
        for txn in transactions(sys.stdin):
            print(txn.iban)
            print(" ", txn.mainrecord)
            for extra in txn.extrarecords:
                print("  ", extra)
        sys.exit(1)

    if 'pikcsv' in sys.argv:
        pass

    if 'pos' in sys.argv:
        selector = lambda x: x.cents > 0
    elif 'neg' in sys.argv:
        selector = lambda x: x.cents < 0
    elif 'nonpikref' in sys.argv:
        selector = lambda x: x.cents > 0 and (not x.ref or not (len(x.ref) == 4 or len(x.ref) == 6))
    else:
        selector = lambda x: True

    def euros(cents):
        return "%.2f" % (cents/100.0)

    o = csv.writer(sys.stdout)
    for txn in transactions(sys.stdin):
        if selector(txn):
            if txn.msg:
                o.writerow([txn.iban, txn.date.strftime("%Y-%m-%d"), txn.name.encode('utf-8'), euros(txn.cents), txn.ref, txn.msg.encode('utf-8'), txn.ourref])
            else:
                o.writerow([txn.iban, txn.date.strftime("%Y-%m-%d"), txn.name.encode('utf-8'), euros(txn.cents), txn.ref, '', txn.ourref])

            
