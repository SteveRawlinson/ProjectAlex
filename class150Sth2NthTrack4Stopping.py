import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Sth2NthTrack4Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory

    def getSpeeds(self):
        return [0.6, 0.3, 0.15]

    def getSlowTimes(self):
        return {"FPK P4": 5, "AAP P1": 5, "NSG P2": 3, "North Link": 4}

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        fast, medium, slow = self.getSpeeds()

        self.loco.status = loco.MOVING
        start = time.time()

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock')
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('FPK P4')
        self.shortJourney(False, self.loco.block, "FPK P4", medium, slowSpeed=slow, routes=routes, lock=lock)
        self.waitAtPlatform()

        # FPK to AAP
        self.shortJourney(False, self.loco.block, "AAP P1", medium, slowSpeed=slow)
        self.waitAtPlatform()

        # AAP to PAL
        self.shortJourney(False, self.loco.block, "NSG P2", medium, slowSpeed=slow)
        self.waitAtPlatform()

        lock = self.getLock('North Link Lock')

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        if self.getJackStatus() == NORMAL and self.loco.rarity() == 0:
            # If this loco has a rarity of zero and we're not shutting down operations
            # there's no point in going all the way to the sidings because we'll just get
            # started up again. Stop on the North Link
            self.debug("stopping early")
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(False, self.loco.block, "North Link", medium, slowSpeed=slow, routes=routes)
        else:
            # PAL to North sidings
            siding = self.loco.selectSiding(NORTH_SIDINGS)
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(False, self.loco.block, "North Link", medium, routes=routes, lock=lock)
            routes = self.requiredRoutes(siding)
            self.shortJourney(False, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'


        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False
