import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Nth2SthTrack1Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory


    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we're in the right place for this journey
        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        start = time.time()
        platformWaitTimeMsecs = self.platformWaitTimeMsecs
        addr = self.loco.dccAddr

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("NSG P1")
        self.shortJourney(True, self.loco.block, "Nth Fast Link", 0.6, routes=routes, lock=lock)
        self.unlock('North Link Lock') # is done anyway by shortJourney but the makes it more readable

        # on to NSG P1
        self.shortJourney(True, self.loco.block, "NSG P1", 0.4, slowSpeed=0.2, slowTime=8000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # PAL to AAP
        self.shortJourney(True, "NSG P1", "AAP P2", 0.4, 0.2, 5000)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # AAP to FPK
        self.shortJourney(True, "AAP P2", "FPK P3", 0.4, 0.25, 11000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to Sth Sidings
        lock = self.getLock('South Link Lock')

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        if siding.getId() == "FP sidings":
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.4, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        else:
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "South Link", 0.4, routes=routes)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False


loc = loco.Loco(2144)
loc.setBlock('Nth Sidings 3')
Class150Nth2SthTrack1Stopping(loc, None).start()