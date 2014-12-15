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
