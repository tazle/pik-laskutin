# -*- coding: utf-8
import datetime as dt

class Flight(object):
    def __init__(self, aircraft, date, account_id, captain_name, student_name, n_on_board, takeoff_location, landing_location, takeoff_time, landing_time, n_landings, purpose, duration, invoicing_comment):
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
        self.purpose = purpose
        self.duration = duration # in minutes
        self.invoicing_comment = invoicing_comment
        self.deleted = False

    @staticmethod
    def generate_from_csv(rows):
        # CSV format
        # maybe with header row
        # Lentokone,Tapahtumapäivä,Maksajan viitenumero,Päällikön viitenumero,Oppilaan viitenumero,Henkilöluku,Lähtöpaikka,Laskeutumispaikka,Lähtöaika,Laskeutumisaika,Lentoaika,Laskuja,Tarkoitus,Lentoaika_desimaalinen,"Laskutuslisä, syy"
        # DDS,2014-03-31,115128,Lehti,Khurshid O.,2,efhf,efhf,13:28,14:34,1:05,5,kou,65,ei viitettä
        # string,ISO8601, string, string, string, int, string, string, hh:mmZ?, hh:mmZ?, hh:mm, string(3), int, string
        
        for row in rows:
            row = [x.decode("utf-8") for x in row]
            try:
                int(row[13])
            except ValueError:
                continue # header row
            date = dt.date(*map(int, row[1].split("-")))
            person_count = int(row[5])
            n_landings = int(row[11])
            duration = int(row[13])
            if _flight_has_different_tz(row[6:7]):
                raise Exception("Flight to weird timezone, times?")
            yield Flight(row[0], date, row[2], row[3], row[4], person_count, row[6], row[7], row[8], row[9], n_landings, row[12], duration, row[14])

def _flight_has_different_tz(locations):
    same_tz = ["ef", "ee"]
    for _loc in locations:
        loc = _loc.lower()
        for acceptable_tz_prefix in same_tz:
            if loc.startswith(acceptable_tz_prefix):
                break
        else:
            return True
    return False
