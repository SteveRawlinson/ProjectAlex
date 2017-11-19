import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class SouthReverseLoopToSouthSidings(alex.Alex):
    def __init__(self, loc):
        self.loco = loc
        self.knownLocation = None

    def handle(self):

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        # check there's a siding that will accommodate us
        siding = self.loco.selectSiding(SOUTH_SIDINGS)

        if self.loco.block is None:
            self.loco.setBlock(SOUTH_REVERSE_LOOP)
        else:
            b = layoutblocks.getLayoutBlock(SOUTH_REVERSE_LOOP).getBlock()
            if self.loco.block != b:
                raise RuntimeError("loco " + self.loco.nameAndAddress() + " is in " + self.loco.block.getDisplayName() + " not South Reverse Loop")

        if self.isBlockOccupied(self.loco.block) is False:
            raise RuntimeError("South Reverse Loop is not occupied")

        lock = self.getLock("South Link Lock")
        self.loco.status = loco.MOVING

        routes = [ROUTEMAP[SOUTH_REVERSE_LOOP][1]] + self.requiredRoutes("FPK P1")
        self.shortJourney(True, self.loco.block, "South Link", 0.3,  stopIRClear=IRSENSORS["South Link Clear"], routes=routes)

        routes = self.requiredRoutes(siding)
        self.shortJourney(False, self.loco.block, siding, 0.4, routes=routes, stopIRClear=IRSENSORS[siding.getId()])

        self.unlock(lock)
        self.loco.status = loco.SIDINGS

        return False


class SouthSidingsToSouthReverseLoop(alex.Alex):
    def __init__(self, loc):
        self.loco = loc
        self.knownLocation = None

    def handle(self):

        # check we have a block and the block is occupied
        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the South Sidings!")
        print "boo"

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.getLock("South Link Lock")
        self.loco.status = loco.MOVING
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("FPK P1")
        self.shortJourney(False, self.loco.block, "South Link", 0.5, routes=routes, stopIRClear=IRSENSORS["South Link Clear"])

        # now go in the reverse loop
        self.loco.forward()
        self.loco.setSpeedSetting(0.4)
        self.reverseLoop(SOUTH_REVERSE_LOOP)
        self.loco.status = loco.SIDINGS

        return False

class NorthReverseLoopToNorthSidings(alex.Alex):
    def __init__(self, loc):
        self.loco = loc
        self.knownLocation = None

    def handle(self):

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        # check there's a siding that will accommodate us
        siding = self.loco.selectSiding(NORTH_SIDINGS)

        if self.loco.block is None:
            self.loco.setBlock(NORTH_REVERSE_LOOP)
        else:
            b = layoutblocks.getLayoutBlock(NORTH_REVERSE_LOOP).getBlock()
            if self.loco.block != b:
                raise RuntimeError("loco " + self.loco.nameAndAddress() + " is in " + self.loco.block.getDisplayName() + " not North Reverse Loop")

        if self.isBlockOccupied(self.loco.block) is False:
            raise RuntimeError("North Reverse Loop is not occupied")

        lock = self.getLock("North Link Lock")
        self.loco.status = loco.MOVING

        routes = [ROUTEMAP[NORTH_REVERSE_LOOP][1]] + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "North Link", 0.5,  stopIRClear=IRSENSORS["North Link Clear"], routes=routes)

        routes = self.requiredRoutes(siding)
        self.shortJourney(False, self.loco.block, siding, 0.4, routes=routes, stopIRClear=IRSENSORS[siding.getId()])

        self.unlock(lock)
        self.loco.status = loco.SIDINGS

        return False


class NorthSidingsToNorthReverseLoop(alex.Alex):
    def __init__(self, loc):
        self.loco = loc
        self.knownLocation = None

    def handle(self):

        # check we have a block and the block is occupied
        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the South Sidings!")
        print "boo"

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.getLock("North Link Lock")
        self.loco.status = loco.MOVING
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(False, self.loco.block, "North Link", 0.5, routes=routes, stopIRClear=IRSENSORS["North Link Clear"])

        # now go in the reverse loop
        self.loco.forward()
        self.loco.setSpeedSetting(0.4)
        self.reverseLoop(NORTH_REVERSE_LOOP)
        self.loco.status = loco.SIDINGS

        return False


loc = loco.Loco(68)
# loc.setBlock(SOUTH_REVERSE_LOOP)
# SouthReverseLoopToSouthSidings(loc).start()
#loc.setBlock("Sth Sidings 2")
#SouthSidingsToSouthReverseLoop(loc).start()
loc.setBlock(NORTH_REVERSE_LOOP)
NorthReverseLoopToNorthSidings(loc).start()
#loc.setBlock("Nth Sidings 4")
#NorthSidingsToNorthReverseLoop(loc).start()