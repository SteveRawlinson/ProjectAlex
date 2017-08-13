import jarray
import jmri
import time
import alex
import loco
from myroutes import *
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')


class Loco2144Sth2NthTrack2(alex.Alex):

    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        self.loco.status = loco.MOVING
        start = time.time()

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock')
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('Sth Hertford Outer')
        self.shortJourney(False, self.loco.block, "FPK P2", 0.4, 0.3, 3000, routes=routes, lock=lock)
        self.waitAtPlatform()

        # FPK to AAP
        self.shortJourney(False, self.loco.block, "AAP P3", 0.4, 0.2, 2000)
        self.waitAtPlatform()

        # AAP to PAL
        self.shortJourney(False, self.loco.block, "PAL P2", 0.4, 0.3, 1000)
        self.waitAtPlatform()

        # PAL to North sidings
        lock = self.getLock('North Link Lock')
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        routes = self.requiredRoutes(self.loco.block)
        self.shortJourney(False, self.loco.block, "North Link", 0.4, routes=routes)
        routes = self.requiredRoutes(siding)
        self.shortJourney(False, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS
        return False

# l = loco.Loco(2144)
# l.initBlock()
# Loco2144Sth2NthTrack2(l).start()
