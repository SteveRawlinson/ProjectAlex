import jmri
import time
import sys

sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassFastSth2NthTrack6Nonstop(alex.Alex):
    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory


    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the south link track
        lock = self.getLock('South Link Lock')

        # Out the sth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("FPK P8")
        self.shortJourney(False, self.loco.block, "South Link", 'fast', routes=routes, dontStop=True)
        self.shortJourney(False, self.loco.block, "FPK P8", 'fast', lock=lock, dontStop=True)

        # All the way to North Fast Outer 2
        self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", 'fast', dontStop=True)

        # get a lock on the north link, but if it's not available immediately ...
        lock = self.getLockNonBlocking('North Link Lock')
        if lock is False:
            # stop the train at North Fast Outer 1
            self.loco.setSpeedSetting('slow')
            time.sleep(8)
            self.loco.setSpeedSetting(0)
            lock = self.getLock('North Link Lock')

        # we got the lock - set the turnouts for Nth Fast Outer 1
        for r in self.requiredRoutes("Nth Fast Outer 1"):
            self.setRoute(r, 0)

        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        # progress to ...
        self.shortJourney(False, self.loco.block, "North Fast Link", 'medium', dontStop=True)
        self.shortJourney(False, self.loco.block, "North Link", 'fast', dontStop=True)

        # select a siding
        b = None
        if not self.loco.reversible():
            b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        if b is not None:
            self.loco.setSpeedSetting('fast')
            self.reverseLoop(NORTH_REVERSE_LOOP)
            self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
            if lock:
                self.unlock(lock)
        else:
            siding = self.loco.selectSiding(NORTH_SIDINGS)
            routes = self.requiredRoutes(siding)
            self.shortJourney(False, self.loco.block, siding, bendSpeed, slowSpeed, stopIRClear=IRSENSORS[siding.getId()],  routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False


