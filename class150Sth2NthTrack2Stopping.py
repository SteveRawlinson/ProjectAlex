import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Sth2NthTrack2Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        self.loco.status = loco.MOVING
        start = time.time()

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock')
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('Sth Hertford Outer')
        self.shortJourney(False, self.loco.block, "FPK P2", 0.4, 0.3, 3000, routes=routes, lock=lock)
        self.waitAtPlatform()

        # FPK to AAP
        self.shortJourney(False, self.loco.block, "AAP P3", 0.4, 0.2, 3000)
        self.waitAtPlatform()

        # AAP to PAL
        self.shortJourney(False, self.loco.block, "PAL P2", 0.4, 0.3, 1000)
        self.waitAtPlatform()

        # PAL to North sidings
        lock = self.getLock('North Link Lock')
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        routes = self.requiredRoutes(self.loco.block)
        self.shortJourney(False, self.loco.block, "North Link", 0.4, routes=routes, lock=lock)
        routes = self.requiredRoutes(siding)
        self.shortJourney(False, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS
        return False

