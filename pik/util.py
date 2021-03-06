# -*- coding: utf-8
import datetime as dt

class Period(object):
    def __init__(self, start, end):
        """
        @param start Start date, inclusive
        @param end End date, inclusive
        """
        self.start = start
        self.end = end

    @staticmethod
    def full_year(year):
        return Period(dt.date(year, 1, 1), dt.date(year, 12, 31))

    def __contains__(self, date):
        return self.start <= date and date <= self.end

def parse_iso8601_date(datestr):
    try:
        return dt.date(*map(int, datestr.split('-')))
    except ValueError, e:
        raise ValueError("Could not parse date %s" %datestr, e)

FORMAT_2015 = "2015"
FORMAT_2014 = "2014"
def format_invoice(invoice, additional_details="", format=FORMAT_2015):

    dateformat = "%d.%m.%Y"
    spacer = "---------------------------"
    due_in = dt.timedelta(14)

    total_price = sum(l.price for l in invoice.lines)

    ret = \
          u"PIK ry jäsenlaskutus, viite %s\n" % invoice.account_id + spacer + "\n"

    if format == FORMAT_2015:
        ret += u"\nLentotilin saldo: %.2f EUR" % (total_price) + "\n" + spacer + "\n\n"
    elif format == FORMAT_2014 and total_price <= 0:
            ret += u"Lentotilin saldo: %.2f EUR" % (total_price) + "\n" + spacer + "\n\n"
        
    if total_price > 0:
        ret += u"Laskun päivämäärä: " + invoice.date.strftime(dateformat) + "\n\n" + \
               u"Saaja: Polyteknikkojen Ilmailukerho ry\n" + \
               u"Saajan tilinumero: FI24 1309 3000 1124 58 (Nordea)\n\n" + \
               u"Viitenumero (PIK-viite): " + invoice.account_id + "\n" + \
               u"Laskun eräpäivä: " + (invoice.date + due_in).strftime(dateformat) + "\n\n" + \
               u"Maksettavaa: %.2f EUR" % (total_price) + "\n" + spacer + "\n\n"
    else:
        if format == FORMAT_2015:
            ret += u"Ei maksettavaa kerholle, ennakkomaksuja kerholla %.2f EUR." %(-total_price) + "\n" + spacer + "\n\n"
        else:
            ret += u"Ei maksettavaa kerholle." + "\n" + spacer + "\n\n"

    ret += additional_details + "\n\n"

    ret += u"Tapahtumien erittely: \n\n"

    for line in sorted(invoice.lines, key=lambda line: line.date):
        if line.price == 0:
            continue
        if format == FORMAT_2015:
            ret += " * "
        ret += "%s %s:  %.2f" % (line.date.strftime(dateformat), line.item, line.price) +"\n"
    ret += "\n"

    ret += u"Myös seuraavat tapahtumat (à 0 EUR) on huomioitu:\n\n"

    for line in sorted(invoice.lines, key=lambda line: line.date):
        if not line.price == 0:
            continue

        
        if format == FORMAT_2015:
            ret += " * "
        ret += u"%s %s" % (line.date.strftime(dateformat), line.item) +"\n"

    return ret
