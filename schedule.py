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




journeys = {}

with open('C:\Users\steve\shortJourney.log', 'r') as fp:
    for line in fp:
        nameAndAddress, startBlock, endBlock, startTime, arriveTime, finishTime, duration = line.split(',')
        j = HistoricJourney(nameAndAddress, startBlock, endBlock)
        if j.id in journeys:
            j = journeys[j.id]
        j.durations.append(Decimal(duration))





