# -*- coding: utf-8
from pik.flights import Flight
from pik.rules import FlightRule, AircraftFilter, PeriodFilter, CappedRule, AllRules, FirstRule, SetDateRule, SimpleRule, SinceDateFilter, ItemFilter, PurposeFilter, InvoicingChargeFilter, TransferTowFilter, NegationFilter, DebugRule, flightFilter, eventFilter, SetLedgerYearRule, PositivePriceFilter, NegativePriceFilter
from pik.util import Period, format_invoice, parse_iso8601_date
from pik.billing import BillingContext, Invoice
from pik.event import SimpleEvent
from pik.hansa import SimpleHansaTransaction, SimpleHansaRow
from pik import nda
import datetime as dt
import csv
import sys
from collections import defaultdict
from itertools import chain, groupby
import json
import os
from itertools import count
import unicodedata
import math
import decimal

def make_rules(ctx=BillingContext()):
    ACCT_PURSI_KEIKKA = 3220
    ACCT_TOW = 3130
    ACCT_DDS = 3101
    ACCT_CAO = 3100
    ACCT_1037 = 3150 # Lentotuntitulot jäseniltä
    ACCT_1037_OPEALE = 3150 # Lentotuntitulot jäseniltä
    ACCT_TOWING = 3170 # Muut lentotoiminnan tulot
    ACCT_PURSI_INSTRUCTION = 3470 # Muut tulot koulutustoiminnasta
    ACCT_KALUSTO = 3010
    ACCT_LASKUTUSLISA = 3610 # Hallinnon tulot

    ID_KM_2014 = "kausimaksu_tot_2014"
    ID_KM_P_2014 = "kausimaksu_pursi_2014"
    ID_KM_M_2014 = "kausimaksu_motti_2014"

    ID_KM_2015 = "kausimaksu_tot_2015"
    ID_KM_P_2015 = "kausimaksu_pursi_2015"
    ID_KM_M_2015 = "kausimaksu_motti_2015"

    ID_KM_2016 = "kausimaksu_tot_2016"
    ID_KM_P_2016 = "kausimaksu_pursi_2016"
    ID_KM_M_2016 = "kausimaksu_motti_2016"

    # Added 2017-10-09:
    ID_KM_2017 = "kausimaksu_tot_2017"
    ID_KM_P_2017 = "kausimaksu_pursi_2017"
    ID_KM_M_2017 = "kausimaksu_motti_2017"

    # Added 2018-11-07:
    ID_KM_2018 = "kausimaksu_tot_2018"
    ID_KM_P_2018 = "kausimaksu_pursi_2018"
    ID_KM_M_2018 = "kausimaksu_motti_2018"
    
    # Added 2019-10-08:
    ID_KM_2019 = "kausimaksu_tot_2019"
    ID_KM_P_2019 = "kausimaksu_pursi_2019"
    ID_KM_M_2019 = "kausimaksu_motti_2019"
    
    # Added 2020-03-15:
    ID_KM_2020 = "kausimaksu_tot_2020"
    ID_KM_P_2020 = "kausimaksu_pursi_2020"
    ID_KM_M_2020 = "kausimaksu_motti_2020"
    
    # Added 2021-11-11:
    ID_KM_2021 = "kausimaksu_tot_2021"
    ID_KM_P_2021 = "kausimaksu_pursi_2021"
    ID_KM_M_2021 = "kausimaksu_motti_2021"

    ID_PK_2014 = "pursikönttä_2014"
    ID_PK_2015 = "pursikönttä_2015"
    ID_PK_2016 = "pursikönttä_2016"
    ID_PK_2017 = "pursikönttä_2017" # Added 2017-10-09
    ID_PK_2018 = "pursikönttä_2018" # Added 2018-11-07
    ID_PK_2019 = "pursikönttä_2019" # Added 2019-10-08
    ID_PK_2020 = "pursikönttä_2020" # Added 2020-03-15
    ID_PK_2021 = "pursikönttä_2021" # Added 2021-11-11

    ID_KK_2014 = "kurssikönttä_2014"
    ID_KK_2015 = "kurssikönttä_2015"
    ID_KK_2016 = "kurssikönttä_2016"
    ID_KK_2017 = "kurssikönttä_2017" # Added 2017-10-09
    ID_KK_2018 = "kurssikönttä_2018" # Added 2018-11-07
    ID_KK_2019 = "kurssikönttä_2019" # Added 2019-10-08
    ID_KK_2020 = "kurssikönttä_2020" # Added 2020-03-15
    ID_KK_2021 = "kurssikönttä_2021" # Added 2021-11-11. Notice that kurssikönttä was discontinued starting 2021

    F_PAST = [PeriodFilter(Period(dt.date(2010,1,1), dt.date(2013,12,31)))]

    F_2014 = [PeriodFilter(Period.full_year(2014))]
    F_FK = [AircraftFilter("650")]
    F_FM = [AircraftFilter("787")]
    F_FQ = [AircraftFilter("733")]
    F_FY = [AircraftFilter("883")]
    F_FI = [AircraftFilter("1035")]
    F_DG = [AircraftFilter("952")]
    F_TK = [AircraftFilter("TK")]
    F_HB = [AircraftFilter("755")]
    F_DDS = [AircraftFilter("DDS")]
    F_CAO = [AircraftFilter("CAO")]
    F_TOW = [AircraftFilter("TOW")]
    F_1037 = [AircraftFilter("1037")]
    F_1037_OPEALE = [AircraftFilter("1037-opeale")]
    F_FK_KURSSIALE = [AircraftFilter("650-kurssiale")]
    F_FM_KURSSIALE = [AircraftFilter("787-kurssiale")]
    F_FQ_KURSSIALE = [AircraftFilter("733-kurssiale")]
    F_FY_KURSSIALE = [AircraftFilter("883-kurssiale")]
    F_FI_KURSSIALE = [AircraftFilter("1035-kurssiale")]
    F_DG_KURSSIALE = [AircraftFilter("952-kurssiale")]
    F_MOTTI = [AircraftFilter("DDS","CAO","TOW","1037","1037-opeale")]
    F_PURTSIKKA = [AircraftFilter("650","787","733","883","952","1035","650-kurssiale","787-kurssiale","733-kurssiale","883-kurssiale","1035-kurssiale","952-kurssiale")]
    F_KAIKKI_KONEET = [AircraftFilter("DDS","CAO","TOW","1037","1037-opeale","650","787","733","883","952","1035","650-kurssiale","787-kurssiale","733-kurssiale","883-kurssiale","1035-kurssiale","952-kurssiale")]
    F_PURSIK = [SinceDateFilter(ctx, ID_PK_2014)]
    F_KURSSIK = [SinceDateFilter(ctx, ID_KK_2014)]
    F_LASKUTUSLISA = [InvoicingChargeFilter()]

    F_2015 = [PeriodFilter(Period.full_year(2015))]
    F_PURTSIKKA_2015 = [AircraftFilter("650","787","733","883","952","TK")]
    F_KAIKKI_KONEET_2015 = [AircraftFilter("DDS","CAO","TOW","650","787","733","883","952","TK")]
    F_PURSIK_2015 = [SinceDateFilter(ctx, ID_PK_2015)]
    F_KURSSIK_2015 = [SinceDateFilter(ctx, ID_KK_2015)]

    F_2016 = [PeriodFilter(Period.full_year(2016))]
    F_PURTSIKKA_2016 = [AircraftFilter("650","787","733","883","952","755")]
    F_KAIKKI_KONEET_2016 = [AircraftFilter("TOW","650","787","733","883","952","755")]
    F_PURSIK_2016 = [SinceDateFilter(ctx, ID_PK_2016)]
    F_KURSSIK_2016 = [SinceDateFilter(ctx, ID_KK_2016)]
    
     # Added 2017-10-09:
    F_2017 = [PeriodFilter(Period.full_year(2017))]
    F_PURTSIKKA_2017 = [AircraftFilter("650","787","733","883","952")]
    F_KAIKKI_KONEET_2017 = [AircraftFilter("TOW","650","787","733","883","952")]
    F_PURSIK_2017 = [SinceDateFilter(ctx, ID_PK_2017)]
    F_KURSSIK_2017 = [SinceDateFilter(ctx, ID_KK_2017)]

    # Added 2018-11-07:
    F_2018 = [PeriodFilter(Period.full_year(2018))]
    F_PURTSIKKA_2018 = [AircraftFilter("650","787","733","883","952")]
    F_KAIKKI_KONEET_2018 = [AircraftFilter("TOW","650","787","733","883","952")]
    F_PURSIK_2018 = [SinceDateFilter(ctx, ID_PK_2018)]
    F_KURSSIK_2018 = [SinceDateFilter(ctx, ID_KK_2018)]
    
    # Added 2019-10-08:
    F_2019 = [PeriodFilter(Period.full_year(2019))]
    F_PURTSIKKA_2019 = [AircraftFilter("650","787","733","883","952","1035")]
    F_KAIKKI_KONEET_2019 = [AircraftFilter("TOW","650","787","733","883","952","1035")]
    F_PURSIK_2019 = [SinceDateFilter(ctx, ID_PK_2019)]
    F_KURSSIK_2019 = [SinceDateFilter(ctx, ID_KK_2019)]

    # Added 2020-03-15:
    F_2020 = [PeriodFilter(Period.full_year(2020))]
    F_PURTSIKKA_2020 = [AircraftFilter("650","787","733","883","952","1035")]
    F_KAIKKI_KONEET_2020 = [AircraftFilter("TOW","1037","1037-opeale","650","787","733","883","952","1035")]
    F_PURSIK_2020 = [SinceDateFilter(ctx, ID_PK_2020)]
    F_KURSSIK_2020 = [SinceDateFilter(ctx, ID_KK_2020)]

    # Added 2021-11-11:
    F_2021 = [PeriodFilter(Period.full_year(2021))]
    F_PURTSIKKA_2021 = [AircraftFilter("650","787","733","883","952","1035","650-kurssiale","787-kurssiale","733-kurssiale","883-kurssiale","1035-kurssiale","952-kurssiale")]
    F_KAIKKI_KONEET_2021 = [AircraftFilter("TOW","1037","1037-opeale","650","787","733","883","952","1035","650-kurssiale","787-kurssiale","733-kurssiale","883-kurssiale","1035-kurssiale","952-kurssiale")]
    F_PURSIK_2021 = [SinceDateFilter(ctx, ID_PK_2021)]
    F_KURSSIK_2021 = [SinceDateFilter(ctx, ID_KK_2021)]



    def pursi_rule(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    def pursi_rule_2015(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2015, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2015, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    def pursi_rule_2016(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2016, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2016, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    # Added 2017-10-09:
    def pursi_rule_2017(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2017, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2017, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    # Added 2018-11-07:
    def pursi_rule_2018(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2018, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2018, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])
                          
    # Added 2019-10-08:
    def pursi_rule_2019(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2019, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2019, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    # Added 2020-03-15:
    def pursi_rule_2020(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2020, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2020, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    # Added 2021-11-11:
    def pursi_rule_2021(base_filters, price, kurssi_price = 0, package_price = 0):
        return FirstRule([FlightRule(package_price, ACCT_PURSI_KEIKKA, base_filters + F_PURSIK_2021, "Lento, pursiköntällä, %(aircraft)s, %(duration)d min"),
                          FlightRule(kurssi_price, ACCT_PURSI_KEIKKA, base_filters + F_KURSSIK_2021, "Lento, kurssiköntällä, %(aircraft)s, %(duration)d min, %(purpose)s"),
                          FlightRule(price, ACCT_PURSI_KEIKKA, base_filters)])

    rules_past = [
        # Normal simple events from the past are OK
        SimpleRule(F_PAST)
    ]

    rules_2014 = [
        FlightRule(171, ACCT_DDS, F_DDS + F_2014),
        FlightRule(134, ACCT_CAO, F_CAO + F_2014),
        FlightRule(146, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2014, 1, 1), dt.date(2014, 3, 31)))]),
        # Variable price for TOW in the second period, based on purpose of flight
        FirstRule([FlightRule(124, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2013, 4, 1), dt.date(2014, 12, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(104, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2013, 4, 1), dt.date(2014, 12, 31)))])
               ]),

        pursi_rule(F_2014 + F_FK, 15),
        pursi_rule(F_2014 + F_FM, 25, 10),
        pursi_rule(F_2014 + F_FQ, 25),
        pursi_rule(F_2014 + F_FY, 32, 17),
        pursi_rule(F_2014 + F_DG, 40),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA + F_2014 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2014, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2014, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, [PeriodFilter(Period.full_year(2014)),
                                                              AircraftFilter("650", "733", "787", "883", "952")],
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2014, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, [PeriodFilter(Period.full_year(2014)),
                                                         AircraftFilter("DDS", "CAO", "TOW"),
                                                         NegationFilter(TransferTowFilter())], # No kalustomaksu for transfer tows
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2014, ctx, SimpleRule(F_2014 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2014, ctx, SimpleRule(F_2014 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2014 + [PositivePriceFilter()]),
                   SimpleRule(F_2014 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2014 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s"),
    ]

    rules_2015 = [
        FlightRule(171, ACCT_DDS, F_DDS + F_2015),
        # Variable price for TOW in the second period, based on purpose of flight
        FirstRule([FlightRule(124, ACCT_TOWING, F_TOW + F_2015 + [TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(104, ACCT_TOW, F_TOW + F_2015)
               ]),

        pursi_rule_2015(F_2015 + F_FK, 15),
        pursi_rule_2015(F_2015 + F_FM, 25, 10),
        pursi_rule_2015(F_2015 + F_FQ, 25),
        pursi_rule_2015(F_2015 + F_FY, 32, 32, 10),
        pursi_rule_2015(F_2015 + F_DG, 40, 10, 10),
        pursi_rule_2015(F_2015 + F_TK, 25, 10, 0),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA + F_2015 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2015, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2015, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2015 + F_PURTSIKKA_2015,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2015, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2015 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2015, ctx, SimpleRule(F_2015 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2015, ctx, SimpleRule(F_2015 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2015 + [PositivePriceFilter()]),
                   SimpleRule(F_2015 + [NegativePriceFilter()])]),


        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2015 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]

    rules_2016 = [
        FlightRule(171, ACCT_DDS, F_DDS + F_2016),
        # Variable price for TOW in the second period, based on purpose of flight
        FirstRule([FlightRule(124, ACCT_TOWING, F_TOW + F_2016 + [TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(104, ACCT_TOW, F_TOW + F_2016)
               ]),

        pursi_rule_2016(F_2016 + F_FK, 15),
        pursi_rule_2016(F_2016 + F_FM, 25, 10),
        pursi_rule_2016(F_2016 + F_FQ, 25),
        pursi_rule_2016(F_2016 + F_FY, 32, 32, 10),
        pursi_rule_2016(F_2016 + F_DG, 40, 10, 10),
        pursi_rule_2016(F_2016 + F_HB, 25, 10, 0),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2016 + F_2016 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2016, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2016, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2016 + F_PURTSIKKA_2016,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2016, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2016 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2016, ctx, SimpleRule(F_2016 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2016, ctx, SimpleRule(F_2016 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2016 + [PositivePriceFilter()]),
                   SimpleRule(F_2016 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2016 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]

    rules_2017 = [
        FlightRule(171, ACCT_DDS, F_DDS + F_2017),
        # Variable price for TOW in the second period, based on purpose of flight
        FirstRule([FlightRule(124, ACCT_TOWING, F_TOW + F_2017 + [TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(104, ACCT_TOW, F_TOW + F_2017)
               ]),

        pursi_rule_2017(F_2017 + F_FK, 15),
        pursi_rule_2017(F_2017 + F_FM, 25, 10),
        pursi_rule_2017(F_2017 + F_FQ, 25),
        pursi_rule_2017(F_2017 + F_FY, 32, 32, 10),
        pursi_rule_2017(F_2017 + F_DG, 40, 10, 10),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2017 + F_2017 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2017, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2017, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2017 + F_PURTSIKKA_2017,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2017, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2017 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2017, ctx, SimpleRule(F_2017 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2017, ctx, SimpleRule(F_2017 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2017 + [PositivePriceFilter()]),
                   SimpleRule(F_2017 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2017 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]
    
    # Added 2018-11-07:
    rules_2018 = [
        # Variable price for TOW, based on purpose of flight
        FirstRule([FlightRule(129, ACCT_TOWING, F_TOW + F_2018 + [TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(129, ACCT_TOW, F_TOW + F_2018)
               ]),

        pursi_rule_2018(F_2018 + F_FK, 15),
        pursi_rule_2018(F_2018 + F_FM, 25, 10),
        pursi_rule_2018(F_2018 + F_FQ, 25),
        pursi_rule_2018(F_2018 + F_FY, 32, 32, 10),
        pursi_rule_2018(F_2018 + F_DG, 40, 10, 10),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2018 + F_2018 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2018, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2018, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2018 + F_PURTSIKKA_2018,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2018, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2018 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2018, ctx, SimpleRule(F_2018 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2018, ctx, SimpleRule(F_2018 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2018 + [PositivePriceFilter()]),
                   SimpleRule(F_2018 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2018 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]
    
    # Added 2019-10-08:
    rules_2019 = [
    
        #FlightRule(129, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2019, 1, 1), dt.date(2019, 4, 6)))]),
        
        # TOW flights 2019-01-01 ... 2019-04-06. Same price for transfer tows and normal flights:
        FirstRule([FlightRule(129, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2019, 1, 1), dt.date(2019, 4, 6))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
           FlightRule(129, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2019, 1, 1), dt.date(2019, 4, 6)))]) 
       ]),
        
        # TOW flights 2019-04-07 ... 2019-05-31. Same price (101) for transfer tows and normal flights:
        # First, check if TOW flight is transfer tow, then fallback to normal TOW flight:
        FirstRule([FlightRule(101, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2019, 4, 7), dt.date(2019, 5, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(101, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2019, 4, 7), dt.date(2019, 5, 31)))]) 
               ]),
        
        # TOW flights 2019-06-01 onwards, as of 2019-11-16. Same price (102) for transfer tows and normal flights:
        # First, check if TOW flight is transfer tow, then fallback to normal TOW flight:
        FirstRule([FlightRule(102, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2019, 6, 1), dt.date(2019, 12, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(102, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2019, 6, 1), dt.date(2019, 12, 31)))]) 
               ]),

        pursi_rule_2019(F_2019 + F_FK, 15),
        pursi_rule_2019(F_2019 + F_FM, 25, 10),
        pursi_rule_2019(F_2019 + F_FQ, 25),
        pursi_rule_2019(F_2019 + F_FY, 32, 32, 10),
        pursi_rule_2019(F_2019 + F_FI, 28, 28),
        pursi_rule_2019(F_2019 + F_DG, 40, 10, 10),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2019 + F_2019 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2019, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2019, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2019 + F_PURTSIKKA_2019,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2019, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2019 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2019, ctx, SimpleRule(F_2019 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2019, ctx, SimpleRule(F_2019 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2019 + [PositivePriceFilter()]),
                   SimpleRule(F_2019 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2019 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]
    
   # Added 2020-03-15:
    rules_2020 = [
    
       
        # OH-TOW variable hourly prices:
        # First, check if TOW flight is transfer tow, then fallback to normal TOW flight:
        FirstRule([FlightRule(102, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2020, 1, 1), dt.date(2020, 3, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(102, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2020, 1, 1), dt.date(2020, 3, 31)))])
                ]),
        # 2020-04-01 - 2020-04-30, 94:
        FirstRule([FlightRule(94, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2020, 4, 1), dt.date(2020, 4, 30))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(94, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2020, 4, 1), dt.date(2020, 4, 30)))])
                ]),
        # 2020-05-01 - 2020-07-31, 90:
        FirstRule([FlightRule(90, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2020, 5, 1), dt.date(2020, 7, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(90, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2020, 5, 1), dt.date(2020, 7, 31)))])
                ]),
        # 2020-08-01 -> 97:
        FirstRule([FlightRule(97, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2020, 8, 1), dt.date(2020, 12, 31))), TransferTowFilter()], "Siirtohinaus, %(duration)d min"),
                   FlightRule(97, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2020, 8, 1), dt.date(2020, 12, 31)))])                   
               ]),


        # OH-1037:
        FlightRule(95, ACCT_1037, F_1037 + F_2020),
        # OH-1037 opeale
        FlightRule(55, ACCT_1037_OPEALE, F_1037_OPEALE + F_2020),


        pursi_rule_2020(F_2020 + F_FK, 15),
        pursi_rule_2020(F_2020 + F_FM, 25, 10),
        pursi_rule_2020(F_2020 + F_FQ, 25),
        pursi_rule_2020(F_2020 + F_FY, 32, 32, 10),
        pursi_rule_2020(F_2020 + F_FI, 28, 28, 5), # Notice new pursikönttä pricing, 5 e/h
        pursi_rule_2020(F_2020 + F_DG, 40, 10, 10),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2020 + F_2020 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2020, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2020, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2020 + F_PURTSIKKA_2020,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2020, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2020 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2020, ctx, SimpleRule(F_2020 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SetDateRule(ID_KK_2020, ctx, SimpleRule(F_2020 + [ItemFilter(".*[kK]urssikönttä.*")])),
                   SimpleRule(F_2020 + [PositivePriceFilter()]),
                   SimpleRule(F_2020 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2020 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]
    

   # Added 2020-11-11:
    rules_2021 = [
    
       
        # OH-TOW variable hourly prices:
        # First, check if TOW flight is transfer tow, then fallback to normal TOW flight:
        # 2020-08-01 -> 97:
        FirstRule([FlightRule(97, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2021, 1, 1), dt.date(2021, 2, 28))), TransferTowFilter()], "Siirtohinaus, TOW, %(duration)d min"),
                   FlightRule(97, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2021, 1, 1), dt.date(2021, 2, 28)))])                   
               ]),
        # 2021-03-01 -> 104
        FirstRule([FlightRule(104, ACCT_TOWING, F_TOW + [PeriodFilter(Period(dt.date(2021, 3, 1), dt.date(2021, 12, 31))), TransferTowFilter()], "Siirtohinaus, TOW, %(duration)d min"),
                   FlightRule(104, ACCT_TOW, F_TOW + [PeriodFilter(Period(dt.date(2021, 3, 1), dt.date(2021, 12, 31)))])                   
               ]),

        # OH-1037:
        FlightRule(95, ACCT_1037, F_1037 + [PeriodFilter(Period(dt.date(2021, 1, 1), dt.date(2021, 3, 24)))]),
        FlightRule(96, ACCT_1037, F_1037 + [PeriodFilter(Period(dt.date(2021, 3, 25), dt.date(2021, 12, 31)))]),

        # OH-1037 opeale
        FlightRule(55, ACCT_1037_OPEALE, F_1037_OPEALE + F_2021),


        pursi_rule_2021(F_2021 + F_FK, 15),
        pursi_rule_2021(F_2021 + F_FM, 25, 10),
        pursi_rule_2021(F_2021 + F_FQ, 25),
        pursi_rule_2021(F_2021 + F_FY, 32, 32, 10),
        pursi_rule_2021(F_2021 + F_FI, 28, 28, 5), # Notice new pursikönttä pricing, 5 e/h
        pursi_rule_2021(F_2021 + F_DG, 40, 40, 10),

        # Kurssiale prices:
        pursi_rule_2021(F_2021 + F_FK_KURSSIALE, 10),
        pursi_rule_2021(F_2021 + F_FM_KURSSIALE, 20, 20),
        pursi_rule_2021(F_2021 + F_FQ_KURSSIALE, 20),
        pursi_rule_2021(F_2021 + F_FY_KURSSIALE, 32, 32, 32),
        pursi_rule_2021(F_2021 + F_FI_KURSSIALE, 28, 28, 28),
        pursi_rule_2021(F_2021 + F_DG_KURSSIALE, 35, 35, 35),

        # Koululentomaksu
        FlightRule(lambda ev: 5, ACCT_PURSI_INSTRUCTION, F_PURTSIKKA_2021 + F_2021 + [PurposeFilter("KOU")], "Koululentomaksu, %(aircraft)s"),

        CappedRule(ID_KM_2021, 90, ctx,
                   AllRules([CappedRule(ID_KM_P_2021, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2021 + F_PURTSIKKA_2021,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min")),
                              CappedRule(ID_KM_M_2021, 70, ctx,
                                         FlightRule(10, ACCT_KALUSTO, F_2021 + F_MOTTI,
                                                         "Kalustomaksu, %(aircraft)s, %(duration)d min"))])),

        # Normal simple events
        FirstRule([SetDateRule(ID_PK_2021, ctx, SimpleRule(F_2021 + [ItemFilter(".*[pP]ursikönttä.*")])),
                   SimpleRule(F_2021 + [PositivePriceFilter()]),
                   SimpleRule(F_2021 + [NegativePriceFilter()])]),

        FlightRule(lambda ev: 2, ACCT_LASKUTUSLISA, F_KAIKKI_KONEET + F_2021 + F_LASKUTUSLISA, "Laskutuslisä, %(aircraft)s, %(invoicing_comment)s")
    ]

    
    
    return rules_past + [SetLedgerYearRule(AllRules(rules_2014), 2014),
                         SetLedgerYearRule(AllRules(rules_2015), 2015),
                         SetLedgerYearRule(AllRules(rules_2016), 2016),
                         SetLedgerYearRule(AllRules(rules_2017), 2017),
                         SetLedgerYearRule(AllRules(rules_2018), 2018),
                         SetLedgerYearRule(AllRules(rules_2019), 2019),
                         SetLedgerYearRule(AllRules(rules_2020), 2020),
                         SetLedgerYearRule(AllRules(rules_2021), 2021)]


def events_to_lines(events, rules):
    for event in events:
        match = False
        for rule in rules:
            for line in rule.invoice(event):
                match = True
                yield line
        if not match:
            print("No match for event", event.__repr__(), file=sys.stderr)

def grouped_lines(lines):
    by_account = defaultdict(lambda: [])
    for line in lines:
        k = line.account_id.upper()
        if any(k.startswith(prefix) for prefix in conf['no_invoicing_prefix']):
            continue
        by_account[line.account_id].append(line)
    return by_account

def events_to_invoices(events, rules, invoice_date=dt.date.today()):
    by_account = grouped_lines(events_to_lines(events, rules))
    for account in sorted(by_account.keys()):
        lines = sorted(by_account[account], key=lambda line: line.date)
        yield Invoice(account, invoice_date, lines)


def write_invoices_to_files(invoices, conf):
    out_dir = conf["out_dir"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    invoice_format_id = conf.get("invoice_format", "2015")
    for invoice in invoices:
        account = invoice.account_id
        with open(os.path.join(out_dir, account + ".txt"), "wb") as f:
            f.write(format_invoice(invoice, conf["description"], invoice_format_id).encode("utf-8"))

def write_hansa_export_file(valid_invoices, invalid_invoices, conf):
    out_dir = conf["out_dir"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    dates = list(map(parse_iso8601_date, conf['hansa_txn_dates']))
    hansa_txn_date_filter = PeriodFilter(Period(*dates))

    hansa_txns = []
    hansa_txn_id_gen = count(conf["hansa_first_txn_id"])
    for invoice in invoices:
        DEBUG = invoice.account_id == "114983"
        lines_by_rule = defaultdict(lambda: [])
        for line in invoice.lines:
            if hansa_txn_date_filter(line):
                lines_by_rule[line.rule].append(line)
            elif DEBUG:
                print("Discarding line because of date filter: %s" %line, file=sys.stderr)

        for (rule, lineset) in lines_by_rule.items():
            # Check all lines have same sign
            signs = [math.copysign(1, line.price) for line in lineset]

            if not (all(sign >= 0 for sign in signs) or all(sign <= 0 for sign in signs)):
                
                print("\n-------------")
                for line_item in lineset:
                    print((line_item.item.encode("utf-8") + ": " + str(line_item.price)))
                    
                print("Inconsistent signs:", (str(item.to_json()) for item in lineset), signs, all(sign >= 0 for sign in signs), all(sign <= 0 for sign in signs), file=sys.stderr)

            # Check all lines have same ledger account, excluding lines that don't go
            # into ledger via this process (they have None as ledger_account_id)
            ledger_accounts = set(line.ledger_account_id for line in lineset) - set([None])
            if len(ledger_accounts) > 1 and not rule.allow_multiple_ledger_categories:
                print("Inconsistent ledger accounts:", ", ".join(str(l) for l in lineset), ledger_accounts, file=sys.stderr)
                
        hansa_rows = []
        for lineset in list(lines_by_rule.values()):
            extract_lai = lambda x: x.ledger_account_id
            for (ledger_account_id, lines) in groupby(sorted(lineset, key=extract_lai), key=extract_lai):
                lines = list(lines)
                if DEBUG:
                    print("Ledger account id:", ledger_account_id, len(lines), file=sys.stderr)
                lines = list(lines)
                if not ledger_account_id:
                    if DEBUG:
                        print("Not going into Hansa:", file=sys.stderr)
                        for line in lines:
                            print(str(line), file=sys.stderr)
                    continue
            
                total_price = sum(line.price for line in lines if line.ledger_account_id)
                if total_price == 0:
                    if DEBUG:
                        print("Not writing hansa line for zero-sum line on account", ledger_account_id, file=sys.stderr)
                    continue
            
                title = os.path.commonprefix([line.item for line in lines])
                if DEBUG:
                    print("Writing hansa line for account", ledger_account_id, "->", total_price, file=sys.stderr)
                if total_price > 0:
                    member_line = SimpleHansaRow(1422, title, debit=total_price)
                    club_line = SimpleHansaRow(ledger_account_id, title, credit=total_price)
                else:
                    member_line = SimpleHansaRow(1422, title, credit=total_price)
                    club_line = SimpleHansaRow(ledger_account_id, title, debit=total_price)
                hansa_rows.append(club_line)
                hansa_rows.append(member_line)

        hansa_rows.sort()

        if hansa_rows:
            hansa_id = next(hansa_txn_id_gen)
            hansa_txn = SimpleHansaTransaction(hansa_id, conf["hansa_year"], conf["hansa_entry_date"], conf["hansa_txn_date"], "Lentolasku, " + invoice.account_id, invoice.account_id, hansa_rows)
            hansa_txns.append(hansa_txn)

    with open(os.path.join(out_dir, "hansa-export-" + conf["invoice_date"] + ".txt"), "wb") as f:
        for txn in hansa_txns:
            f.write(unicodedata.normalize("NFC", txn.hansaformat()).encode("iso-8859-15"))

def write_total_csv(invoices, fname):
    import csv
    writer = csv.writer(open(fname, 'wb'))
    writer.writerows(invoice.to_csvrow_total() for invoice in invoices)

def write_row_csv(invoices, fname_template):
    import unicodecsv
    by_year = defaultdict(lambda: [])
    for invoice in invoices:
        for line in invoice.lines:
            if not line.rollup:
                row = line.to_csvrow()
                by_year[row.ledger_year].append(row)
    for year, yearly_rowset in by_year.items():
        writer = unicodecsv.writer(open(fname_template%year, 'wb'), encoding='utf-8')
        writer.writerows(yearly_rowset)

def is_invoice_zero(invoice):
    return abs(invoice.total()) < 0.01

def make_event_validator(pik_ids, external_ids):
    def event_validator(event):
        if not isinstance(event.account_id, str):
            raise ValueError("Account id must be string, was: " + repr(event.account_id) + " in " + str(event))
        if not ((event.account_id in pik_ids and len(event.account_id) in (4,6)) or
                event.account_id in external_ids):
            raise ValueError("Invalid id was: " + repr(event.account_id) + " in " + str(event).encode("utf-8"))
        return event
    return event_validator

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def read_pik_ids(fnames):
    result = []
    for fname in fnames:
        result.extend(x.strip() for x in open(fname, 'rb').readlines() if x.strip())
    return result

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: invoice-flights.py <conf-file>")
        sys.exit(1)
    conf = json.load(open(sys.argv[1], 'rb'))

    sources = []

    ctx = BillingContext()
    if "context_file_in" in conf:
        context_file = conf["context_file_in"]
        if os.path.isfile(context_file):
            ctx = BillingContext.from_json(json.load(open(context_file, "r"), parse_float=decimal.Decimal))
    rules = make_rules(ctx)

    for fname in conf['event_files']:
        reader = csv.reader(open(fname, 'rb'))
        sources.append(SimpleEvent.generate_from_csv(reader))

    for fname in conf['flight_files']:
        reader = csv.reader(open(fname, "rb"))
        sources.append(Flight.generate_from_csv(reader))

    for fname in conf['nda_files']:
        bank_txn_date_filter = lambda txn_date: True
        if 'bank_txn_dates' in conf:
            dates = list(map(parse_iso8601_date, conf['bank_txn_dates']))
            bank_txn_date_filter = PeriodFilter(Period(*dates))

        reader = nda.transactions(open(fname, 'rb'))
        # Only PIK references and incoming transactions - note that the conversion reverses the sign of the sum, since incoming money reduces the account's debt
        sources.append(SimpleEvent.generate_from_nda(reader, ["FI2413093000112458"], lambda event: bank_txn_date_filter(event) and event.cents > 0 and event.ref and (len(event.ref) == 4 or len(event.ref) == 6)))

    invoice_date = parse_iso8601_date(conf['invoice_date'])
    event_validator = make_event_validator(read_pik_ids(conf['valid_id_files']), conf['no_invoicing_prefix'])
    events = list(sorted(chain(*sources), key=lambda event: event.date))
    for event in events:
        try:
            event_validator(event)
        except ValueError as e:
            print("Invalid account id", event.account_id, str(event), file=sys.stderr)

    invoices = list(events_to_invoices(events, rules, invoice_date=invoice_date))

    valid_invoices = [i for i in invoices if not is_invoice_zero(i)]
    invalid_invoices = [i for i in invoices if is_invoice_zero(i)]

    out_dir = conf["out_dir"]
    if os.path.exists(out_dir):
        raise ValueError("out_dir already exists: " + out_dir)

    total_csv_fname = conf.get("total_csv_name", os.path.join(out_dir, "totals.csv"))
    row_csv_fname_template = conf.get("row_csv_name_template", os.path.join(out_dir, "rows_%s.csv"))

    write_invoices_to_files(valid_invoices, conf)
    write_invoices_to_files(invalid_invoices, conf)
    write_hansa_export_file(valid_invoices, invalid_invoices, conf)
    write_total_csv(invoices, total_csv_fname)
    write_row_csv(invoices, row_csv_fname_template)
    if "context_file_out" in conf:
        json.dump(ctx.to_json(), open(conf["context_file_out"], "w"), cls=DecimalEncoder)

    machine_readable_invoices = [invoice.to_json() for invoice in invoices]

    #print json.dumps(machine_readable_invoices)

    invalid_account = []
    invalid_sum = []

    print("Difference, valid invoices, total", sum(i.total() for i in valid_invoices), file=sys.stderr)
    print("Owed to club, invoices, total", sum(i.total() for i in valid_invoices if i.total() > 0), file=sys.stderr)
    print("Owed by club, invoices, total", sum(i.total() for i in valid_invoices if i.total() < 0), file=sys.stderr)

    print("Zero invoices, count ", len(invalid_invoices), file=sys.stderr)

