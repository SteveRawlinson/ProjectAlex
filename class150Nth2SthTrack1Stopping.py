import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

# alex.sensors = sensors  # explicitly add to auto namespace
# alex.memories = memories
# alex.routes = routes
# alex.layoutblocks = layoutblocks
# alex.ACTIVE = ACTIVE


class Class150Nth2SthTrack1Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory


    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the north sidings!")

        self.loco.status = loco.MOVING

        start = time.time()
        platformWaitTimeMsecs = self.platformWaitTimeMsecs
        addr = self.loco.dccAddr

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", 0.6, routes=routes, lock=lock)
        self.unlock('North Link Lock') # is done anyway by shortJourney but the makes it more readable

        # on to PAL P1
        self.shortJourney(True, self.loco.block, "PAL P1", 0.4, slowSpeed=0.2, slowTime=6000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # PAL to AAP
        self.shortJourney(True, "PAL P1", "AAP P4", 0.4, 0.2, 5000)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # AAP to FPK
        self.shortJourney(True, "AAP P4", "FPK P1", 0.4, 0.25, 11000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to Sth Sidings
        lock = self.getLock('South Link Lock')

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        if siding.getID() == "FP sidings":
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.4, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)
        else:
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "South Link", 0.4, routes=routes)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS


        return False


