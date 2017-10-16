import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassA4Sth2NthTrack4Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock')
        if self.loco.inReverseLoop():
            routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('FPK P4')
        else:
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('FPK P4')
        self.shortJourney(True, self.loco.block, "FPK P4", 0.5, 0.4, 11000, routes=routes, lock=lock)
        self.waitAtPlatform()

        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P1", 0.5, passBlock=True)

        # see if we can get a lock but don't wait for one
        lock = self.getLockNonBlocking('North Link Lock')
        if lock is False:
            # we didn't get a lock, stop at the signal
            self.shortJourney(True, self.loco.block, "NSG P2", 0.5, 0.4, 8000)
            # now wait for a lock
            lock = self.getLock('North Link Lock')
        else:
            # we got the lock - AAP to NSG
            routes = self.requiredRoutes("NSG P2")
            self.shortJourney(True, self.loco.block, "NSG P2", 0.5, routes=routes, passBlock=True)

        # NSG to North sidings
        b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        if b is not None:
            self.setRoute("Welwyn Outer")
            self.loco.setSpeedSetting(0.5)
            self.reverseLoop(NORTH_REVERSE_LOOP)
            self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
            if lock is not None:
                self.unlock(lock)
        else:
            siding = self.loco.selectSiding(NORTH_SIDINGS)
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "North Link", 0.4, routes=routes, lock=lock)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            self.loco.unselectSiding(siding)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False

loc = loco.Loco(68)
loc.setBlock("Sth Reverse Loop")
ClassA4Sth2NthTrack4Stopping(loc, None).start()