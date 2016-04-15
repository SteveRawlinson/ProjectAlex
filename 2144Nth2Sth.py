import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

alex.sensors = sensors  # explicitly add to auto namespace
alex.memories = memories
alex.routes = routes
alex.layoutblocks = layoutblocks
alex.ACTIVE = ACTIVE


class Loco2144Nth2Sth(alex.Alex):
        
    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        start = time.time()
        platformWaitTimeMsecs = self.platformWaitTimeMsecs
        addr = self.loco.dccAddr

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')
        if lock is False:
            return False 

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", 0.6, routes=routes, lock=lock)
        self.unlock('North Link Lock') # is done anyway by shortJourney but the makes it more readable

        # on to PAL P1
        self.shortJourney(True, self.loco.block, "PAL P1", 0.4, slowSpeed=0.2, slowTime=6000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        
        # PAL to AAP
        rc = self.shortJourney(True, "PAL P1", "AAP P4", 0.4, 0.2, 5000)
        if rc is False:
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # AAP to FPK
        rc = self.shortJourney(True, "AAP P4", "FPK P1", 0.4, 0.25, 11000)
        if rc is False:
            return False
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to Sth Sidings
        rc = self.getLock('South Link Lock')
        if rc is False:
            return False
        # set routes to sth sidings
        siding = self.loco.shortestBlockTrainFitsBlocking(SOUTH_SIDINGS)
        print addr, "selected siding", siding.getID()
        routes = self.requiredRoutes("FPK P1") + self.requiredRoutes(siding)
        rc = self.shortJourney(True, "FPK P1", siding, 0.4, 0.2, 0, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)
        if rc is False:
            return False
        self.unlock('South Link Lock')

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False

l = loco.Loco(2144)
l.initBlock()
Loco2144Nth2Sth(l).start()
