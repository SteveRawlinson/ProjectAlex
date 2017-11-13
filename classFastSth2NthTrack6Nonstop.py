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

    # This method should be overridden by the child classes
    def getSpeeds(self):
        return [0.3, 0.2, 0.1]

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        fullSpeed, bendSpeed, slowSpeed = 'fast', 'bend', 'slow'

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the south link track
        lock = self.getLock('South Link Lock')

        # Out the sth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("FPK P8")
        self.shortJourney(False, self.loco.block, "South Link", bendSpeed, routes=routes, dontStop=True)
        self.shortJourney(False, self.loco.block, "FPK P8", fullSpeed, lock=lock)

        # All the way to North Fast Outer 2
        self.shortJourney(False, self.loco.block, "Nth Fast Outer 2", fullSpeed)

        # get a lock on the north link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('North Link Lock')
        if lock is False:
            # stop the train at North Fast Outer 1
            self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", fullSpeed, slowSpeed, 5000)
            # wait for a lock
            lock = self.getLock('North Link Lock')
        else:
            # we got the lock - set the turnouts for Nth Fast Outer 1
            for r in self.requiredRoutes("Nth Fast Outer 1"):
                self.setRoute(r, 0)
            # progress to ...
            self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", fullSpeed, dontStop=True)
            # check we still have the lock
            rc = self.checkLock(lock)
            if rc is False :
                # we lost it, abort!
                self.throttle.setSpeedSetting(0)
                print loco, "race conditions on South Link Lock? Exiting"
                return False

        # select a siding
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        routes = self.requiredRoutes(siding)
        self.shortJourney(False, self.loco.block, siding, bendSpeed, slowSpeed, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        return False

# Javelin
class Loco5004Sth2NthTrack6Nonstop(ClassFastSth2NthTrack6Nonstop):
    pass

# Eurostar
class Loco3213Sth2NthTrack6Nonstop(ClassFastSth2NthTrack6Nonstop):
    pass

# Ave Talgo
class Loco6719Sth2NthTrack6Nonstop(ClassFastSth2NthTrack6Nonstop):
    pass

# Class 91
class Loco1124Sth2NthTrack6Nonstop(ClassFastSth2NthTrack6Nonstop):
    pass


