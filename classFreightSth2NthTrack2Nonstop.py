import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnySth2NthTrack2Nonstop(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we are facing the right way
        if not self.loco.reversible() and self.loco.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        fast = self.loco.speed('fast')
        medium = self.loco.speed('medium')
        slow = self.loco.speed('slow')

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock')
        if self.loco.inReverseLoop():
            routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('FPK P2')
        else:
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('FPK P2')
        self.shortJourney(True, self.loco.block, "South Link", fast, routes=routes, dontStop=True)
        self.shortJourney(True, self.loco.block, "FPK P2", medium, lock=lock, dontStop=True)

        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P3", medium, dontStop=True)

        # AAP to PAL
        self.shortJourney(True, self.loco.block, "PAL P2", medium, dontStop=True)

        # see if we can get a lock but don't wait for one
        lock = self.getLockNonBlocking('North Link Lock')
        routes = self.requiredRoutes(self.loco.block)
        if lock is False:
            # we didn't get a lock, stop at the signal
            self.loco.setSpeedSetting('slow')
            time.sleep(8)
            self.loco.setSpeedSetting(0)
            # now wait for a lock
            lock = self.getLock('North Link Lock')

        # one way or another we now have the lock
        self.shortJourney(True, self.loco.block, 'North Link', medium, routes=routes, dontStop=True)

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        # into North sidings
        b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        if b is not None:
            self.loco.setSpeedSetting(fast)
            self.reverseLoop(NORTH_REVERSE_LOOP)
            self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
            if lock:
                self.unlock(lock)
        else:
            self.debug("North Reverse Loop unavailable")
            siding = self.loco.selectSiding(NORTH_SIDINGS)
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "North Link", medium, routes=routes, lock=lock)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            self.loco.unselectSiding(siding)
            self.loco.wrongway = True

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'

        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False

class Class47Sth2NthTrack2Nonstop(ClassAnySth2NthTrack2Nonstop):
    pass

loc = loco.Loco(7405)
loc.setBlock(SOUTH_REVERSE_LOOP)
Class47Sth2NthTrack2Nonstop(loc, None).start()