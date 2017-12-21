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

    def id(self):
        return self.nameAndAddress + '-' + self.startblock + '-' + self.endblock


    def calc(self):
        count = 0
        tot = Decimal(0.0)
        for d in self.durations:
            if self.min is None or d < self.min: self.min = d
            if self.max is None or d > self.max: self.max = d
            tot += d
            count += 1
        self.average = tot / count

    def to_s(self):
        return self.nameAndAddress + ' ' + self.startblock + ' ' + self.endblock + ' ' + str(self.average)

journeys = {}

with open('C:\Users\steve\shortJourney.log', 'r') as fp:
    for line in fp:
        nameAndAddress, startBlock, endBlock, startTime, arriveTime, finishTime, duration = line.split(',')
        j = HistoricJourney(nameAndAddress, startBlock, endBlock)
        if j.id in journeys:
            j = journeys[j.id]
        j.durations.append(Decimal(duration))

for j in journeys:
    j.calc()
    print j.to_s()




