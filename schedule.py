import re
from decimal import *

class schedule:
    pass

class HistoricJourney:
    def __init__(self, nameAndAddress, startBlock, endBlock):
        self.startblock = startBlock
        self.endblock = endBlock
        self.average = None
        self.count = 0
        self.min = None
        self.max = None
        self.nameAndAddress = nameAndAddress
        self.durations = []

    def dccAddr(self):
       s = re.sub("^[^(]*\(", "", self.nameAndAddress)
       s2 = re.sub("\).*$", "", s)
       return s2

    def id(self):
        return self.dccAddr() + '-' + self.startblock + '-' + self.endblock


    def calc(self):
        tot = Decimal(0.0)
        for d in self.durations:
            if self.min is None or d < self.min: self.min = d
            if self.max is None or d > self.max: self.max = d
            tot += d
            self.count += 1
        self.average = tot / self.count

    def to_s(self):
        return self.nameAndAddress + ' ' + self.startblock + ' ' + self.endblock + ' ' + str(self.average) + ' ' + str(self.count)


print "schedule"
journeys = {}

with open('C:\Users\steve\shortJourney.log', 'r') as fp:
    for line in fp:
        nameAndAddress, startBlock, endBlock, startTime, arriveTime, finishTime, duration = line.split(',')
        j = HistoricJourney(nameAndAddress, startBlock, endBlock)
        if j.id() in journeys:
            j = journeys[j.id()]
        else:
            journeys[j.id()] = j
        j.durations.append(Decimal(duration))

print "there are " + str(len(journeys)) + " journeys"
for k in sorted(journeys.iterkeys()):
    j = journeys[k]
    j.calc()
    print j.to_s()




