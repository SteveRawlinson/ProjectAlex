import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *
import lock

class ClassA4Sth2NthTrack2Stopping(alex.Alex):


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
        # lock = self.getLock('South Link Lock')
        # if self.loco.inReverseLoop():
        #     routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('FPK P2')
        # else:
        #     routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('FPK P2')
        # self.shortJourney(True, self.loco.block, "FPK P2", 0.5, 0.4, 11000, routes=routes, lock=lock)
        # self.waitAtPlatform()

        self.leaveSouthSidings('FPK P2')

        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P3", 'medium', dontStop=True)

        # AAP to PAL
        self.shortJourney(True, self.loco.block, "PAL P2", 'medium', 'slow')

        # see if we can get a lock but don't wait for one
        lck = lock.Lock()
        lck.getLockNonBlocking(NORTH)
        if lck.empty():
            # we didn't get a lock, stop at the signal
            self.loco.graduallyChangeSpeed('slow')
            time.sleep(self.getSlowtime('PAL P2'))
            # now wait for a lock

        # # NSG to North sidings
        # b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        # if b is not None:
        #     self.setRoute("Hertford Nth Outer")
        #     self.loco.setSpeedSetting(0.5)
        #     self.reverseLoop(NORTH_REVERSE_LOOP)
        #     self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
        #     if lock is not None:
        #         self.unlock(lock)
        # else:
        #     siding = self.loco.selectSiding(NORTH_SIDINGS)
        #     routes = self.requiredRoutes(self.loco.block)
        #     self.shortJourney(True, self.loco.block, "North Link", 0.4, routes=routes, lock=lock)
        #     routes = self.requiredRoutes(siding)
        #     self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        #     self.loco.unselectSiding(siding)
        #     self.loco.wrongway = True

        self.moveIntoNorthSidings(lck)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False
