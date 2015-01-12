# -*- coding: utf-8 -*-
import datetime as dt

def findrecord(records, maintype, subtype):
    for record in records:
        if record.type == maintype and record.subtype == subtype:
            return record
    return None

def ordify(d):
    result = {}
    for k,v in d.iteritems():
        result[ord(k)] = ord(v)
    return result

debanktable = ordify({u'[':u'Ä', u'\\':u'Ö', u']':u'Å',
                    u'{':u'ä', u'|':u'ö'})


def debank(str):
    u = str.decode('latin-1')
    return u.translate(debanktable)

class Transaction(object):
    def __init__(self, metarecord, mainrecord, extrarecords=[]):
        self.iban = metarecord.iban
        self.bic = metarecord.bic
        self.date = mainrecord.date
        self.name = mainrecord.name
        self.cents = mainrecord.cents
        self.extrarecords = extrarecords
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
    def date(self):
        datestr = self.str[1+2+3+6+18:1+2+3+6+18+6]
        return dt.datetime.strptime(datestr, "%y%m%d").date()

    @property
    def name(self):
        return debank(self.str[108:108+35]).rstrip(' ')

    @property
    def cents(self):
        sign = self.str[87:88]
        num = self.str[88:88+18]
        return int(sign + num.lstrip('0'))

    @property
    def ref(self):
        ref = self.str[159:159+20].lstrip(' ')
        if ref:
            return ref.lstrip('0')
        else:
            return None

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

    def __repr__(self):
        return "Record11(%s, %s, %s)" %(self.type, self.subtype, self.str.strip())

def transactions(lines):
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

            
