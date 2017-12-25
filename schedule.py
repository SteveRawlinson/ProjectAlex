import re
from decimal import *

class schedule:
    pass

class HistoricJourney:
    def __init__(self, nameAndAddress, startBlock, endBlock):
        self.startblock = startBlock
        self.endblock = endBlock
        self.average = None
        self.min = None
        self.max = None
        self.nameAndAddress = nameAndAddress
        self.durations = []

    def dccAddr(self):
       s = re.sub("^[^\(]*\(", "", self.nameAndAddress)
       s2 = re.sub("\).*$", "", s)
       return s2

    def id:
        return self.nameAndAddress + '-' + self.startblock + '-' + self.endblock

    def calcs(self):
        count = 0
        tot = Deceimal('0.0')
        for d in self.durations:
            if self.min is None or self.min > d:
                self.min = d
            if self.max is None or self.max < d:
                self.max = d
            tot =+ d
            count += 1
        self.average = tot / count

    def to_s(self):
        return "loco: " + self.nameAndAddress + " start: " + self.startblock + " end: " + self.endblock + " avg: " + str(self.average)





journeys = {}

with open('C:\Users\steve\shortJourney.log', 'r') as fp:
    for line in fp:
        nameAndAddress, startBlock, endBlock, startTime, arriveTime, finishTime, duration = line.split(',')
        j = HistoricJourney(nameAndAddress, startBlock, endBlock)
        if j.id in journeys:
            j = journeys[j.id]
        j.durations.append(Decimal(duration))


for k in journeys:
    j = journeys[k]
    j.calcs()
    print j.to_s()


