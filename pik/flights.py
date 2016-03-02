# -*- coding: utf-8
import datetime as dt

ALLOWED_PURPOSES = set(["GEO", "HAR", "HIN", "KOE", "KOU", "LAN", "LAS", "LVL", "MAT", "PALO", "RAH", "SAI", "SAR", "SII", "TAI", "TAR", "TIL", "VLL", "VOI", "YLE", "MUU", "KIL", "TYY"])

class Flight(object):
    def __init__(self, aircraft, date, account_id, captain_name, student_name, n_on_board, takeoff_location, landing_location, takeoff_time, landing_time, n_landings, purpose, duration, invoicing_comment, extra_comments="", transfer_tow=False):
        self.aircraft = aircraft
        self.date = date # date object
        self.account_id = account_id
        self.captain_name = captain_name
        self.student_name = student_name
        self.n_on_board = n_on_board
        self.takeoff_location = takeoff_location
        self.landing_location = landing_location
        self.takeoff_time = takeoff_time
        self.landing_time = landing_time
        self.n_landings = n_landings
        self.purpose = purpose.upper()
        if self.purpose not in ALLOWED_PURPOSES:
            raise ValueError("Invalid prpose of flights: %s, allowed values are: %s" %(purpose, ALLOWED_PURPOSES))
        self.duration = duration # in minutes
        self.invoicing_comment = invoicing_comment
        self.extra_comments = extra_comments
        self.transfer_tow = transfer_tow
        self.deleted = False

    def __unicode__(self):
        return "Flight(" + ", ".join([self.date.isoformat(), self.aircraft, self.account_id]) + ")"

    @staticmethod
    def generate_from_csv(rows):
        # CSV format
        # maybe with header row
        # Lentokone,Tapahtumapäivä,Maksajan viitenumero,Päällikön viitenumero,Oppilaan viitenumero,Henkilöluku,Lähtöpaikka,Laskeutumispaikka,Lähtöaika,Laskeutumisaika,Lentoaika,Laskuja,Tarkoitus,Lentoaika_desimaalinen,"Laskutuslisä, syy",Lisätiedot,Siirtohinaus
        # DDS,2014-03-31,115128,Lehti,Khurshid O.,2,efhf,efhf,13:28,14:34,1:05,5,kou,65,ei viitettä,,
        # string,ISO8601, string, string, string, int, string, string, hh:mmZ?, hh:mmZ?, hh:mm, string(3), int, string, string, 1/0
        #
        # The last two fields are optional
        maybe_header = True
        for row in rows:
            row = [x.decode("utf-8") for x in row]
            if maybe_header:
                maybe_header = False
                try:
                    int(row[13])
                except ValueError:
                    continue # header row
            try:
                date = dt.date(*map(int, row[1].split("-")))
                person_count = int(row[5])
                n_landings = int(row[11])
                duration = int(row[13])
                if _flight_has_different_tz(row[6:7]):
                    raise Exception("Flight to weird timezone, times?")

                if len(row) <= 16:
                    yield Flight(row[0], date, row[2], row[3], row[4], person_count, row[6], row[7], row[8], row[9], n_landings, row[12], duration, row[14])
                elif len(row) >= 17:
                    yield Flight(row[0], date, row[2], row[3], row[4], person_count, row[6], row[7], row[8], row[9], n_landings, row[12], duration, row[14], row[15], bool(row[16]))
                else:
                    raise ValueError(row)
            except Exception, e:
                raise ValueError("Unable to parse line %s" %row, e)

def _flight_has_different_tz(locations):
    same_tz = ["ef", "ee", "zz", "pirtti"]
    for _loc in locations:
        loc = _loc.lower()
        for acceptable_tz_prefix in same_tz:
            if loc.startswith(acceptable_tz_prefix):
                break
        else:
            return True
    return False
