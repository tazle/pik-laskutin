from pik.flights import Flight
import csv
import sys

reader = csv.reader(sys.stdin)

for flight in Flight.generate_from_csv(reader):
    print flight
