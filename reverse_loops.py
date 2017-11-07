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

    def handle(self):

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        # check there's a siding that will accommodate us
        siding = self.loco.selectSiding(SOUTH_SIDINGS)

        if self.loco.block is None:
            self.loco.setBlock(SOUTH_REVERSE_LOOP)
        else:
            b = layoutblocks.getBlock(SOUTH_REVERSE_LOOP).getBlock()
            if self.loco.block != b:
                raise RuntimeError("loco " + self.loco.nameAndAddress() + " is in " + self.loco.block.getDisplayName() + " not South Reverse Loop")

        if not self.loco.blockIsOccupied():
            raise RuntimeError("South Reverse Loop is not occupied")

        lock = self.getLock("South Link Lock")
        self.loco.status = loco.MOVING

        routes = [ROUTEMAP[SOUTH_REVERSE_LOOP[1]]]
        self.shortJourney(True, self.loco.block, "South Link", 0.5,  stopIRClear=IRSENSORS["South Link Clear"], routes=routes)

        routes = ROUTEMAP[siding]
        self.shortJourney(False, self.loco.block, siding, 0.5, routes=routes)

        self.unlock(lock)
        self.loco.status = loco.SIDINGS

        return False


class SouthSidingsToSouthReverseLoop(alex.Alex):
    def __init__(self, loc):
        self.loco = loc

    def handle(self):

        # check we have a block and the block is occupied
        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the South Sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        lock.getLock("South Link Lock")
        self.loco.status = loco.MOVING
        routes = ROUTEMAP[self.loco.block]
        self.shortJourney(False, self.loco.block, "South Link", 0.5, routes=routes, stopIRClear=IRSENSORS["South Link Clear"])

        routes = [ROUTEMAP[SOUTH_REVERSE_LOOP[0]]]
        self.shortJourney(True, self.loco.block, SOUTH_REVERSE_LOOP, 0.5, routes=routes, stopIRClear=IRSENSORS[SOUTH_REVERSE_LOOP])
        self.unlock(lock)
        self.loco.status = loco.SIDINGS

        return False
