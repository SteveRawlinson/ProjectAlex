import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Loco5144Nth2SthTrack5(alex.Alex):
        
    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        self.loco.status = loco.MOVING

        start = time.time()
        platformWaitTimeMsecs = self.platformWaitTimeMsecs
        addr = self.loco.dccAddr

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("NSG P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", 0.6, routes=routes, lock=lock)
        self.unlock('North Link Lock')  # is done anyway by shortJourney but the makes it more readable

        # on to NSG P1
        self.shortJourney(True, self.loco.block, "NSG P1", 0.4, slowSpeed=0.2, slowTime=6000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        
        # NSG to AAP
        self.shortJourney(True, self.loco.block, "AAP P2", 0.4, 0.2, 5000)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # AAP to FPK
        self.shortJourney(True, "AAP P2", "FPK P3", 0.4, 0.25, 11000)
        print addr, "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to Sth Sidings
        self.getLock('South Link Lock')

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        if siding.getID() == "FP sidings":
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.4, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)
        else:
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "North Link", 0.4, routes=routes)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False

# l = loco.Loco(2144)
# l.initBlock()
# Loco2144Nth2SthTrack(l).start()
