import jmri
import time
import sys

sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassAnySth2NthTrack6(alex.Alex):

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # set the direction
        if self.loco.reversible():
            dir = False
        else:
            dir = True

        # get a 'lock' on the south link track
        lock = self.getLock('South Link Lock')

        # Out the sth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("FPK P8")
        self.shortJourney(dir, self.loco.block, "South Link", 'fast', routes=routes, dontStop=True)
        if 'Stopping' in type(self).__name__:
            self.shortJourney(dir, self.loco.block, "FPK P8", 'medium', 'slow', lock=lock)
            self.waitAtPlatform()
        else:
            self.shortJourney(dir, self.loco.block, "FPK P8", 'medium', lock=lock, dontStop=True)

        # All the way to North Fast Outer 1
        self.shortJourney(dir, self.loco.block, "Nth Fast Outer 1", 'medium', dontStop=True)

        # get a lock on the north link, but if it's not available immediately ...
        lock = self.getLockNonBlocking('North Link Lock')
        if lock is False:
            # stop the train at North Fast Outer 1
            self.loco.setSpeedSetting('slow')
            st = self.getSlowTime("NORTH FAST")
            if st is None:
                st = 8
            self.debug("waiting slowtime at NORTH FAST: "+ str(slowTime / 1000))
            time.sleep(st)
            self.loco.setSpeedSetting(0)
            lock = self.getLock('North Link Lock')

        # we got the lock - set the turnouts for Nth Fast Outer 1
        for r in self.requiredRoutes("Nth Fast Outer 1"):
            self.setRoute(r, 0)

        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        # progress to ...
        self.shortJourney(dir, self.loco.block, "Nth Fast Link", 'medium', dontStop=True)
        self.shortJourney(dir, self.loco.block, "North Link", 'fast', dontStop=True)

        self.moveIntoNorthSidings(lock)

        # # select a siding
        # b = None
        # if not self.loco.reversible():
        #     b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        # if b is not None:
        #     self.loco.setSpeedSetting('fast')
        #     self.reverseLoop(NORTH_REVERSE_LOOP)
        #     self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
        #     if lock:
        #         self.unlock(lock)
        # else:
        #     siding = self.loco.selectSiding(NORTH_SIDINGS)
        #     routes = self.requiredRoutes(siding)
        #     self.shortJourney(dir, self.loco.block, siding, 'fast', 'slow', stopIRClear=IRSENSORS[siding.getId()],  routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False

class Class47Sth2NthTrack6Nonstop(ClassAnySth2NthTrack6):
    pass

class ClassA4Sth2NthTrack6Stopping(ClassAnySth2NthTrack6):
    pass

class ClassA4Sth2NthTrack6Nonstop(ClassAnySth2NthTrack6):
    pass

# loc = loco.Loco(68)
# loc.setBlock(SOUTH_REVERSE_LOOP)
# ClassA4Sth2NthTrack6Stopping(loc, None).start()
