import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnyNth2SthTrack5(alex.Alex):

    def handle(self):
        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the north sidings")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        # self.loco.status = loco.MOVING
        #
        # # get a 'lock' on the north link track
        # lock = self.getLock('North Link Lock')
        #
        # # Out the nth sidings
        # routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("Nth Fast Inner 1")
        # sp = self.loco.speed('northSidings') or self.loco.speed('fast')
        # self.shortJourney(True, self.loco.block, "North Link", sp, routes=routes, dontStop=True)
        # self.shortJourney(True, self.loco.block, "Nth Fast Link", 'fast', dontStop=True)
        #
        # # slower round the bend
        # self.shortJourney(True, self.loco.block, "Nth Fast Inner 1", 'northFastBend', lock=lock, dontStop=True)

        self.leaveNorthSidings('Nth Fast Inner 1')

        # off to the other side of the layout
        self.shortJourney(True, self.loco.block, "Sth Fast Inner 2", 'medium', dontStop=True)

        if 'Stopping' in type(self).__name__:
            self.shortJourney(True, self.loco.block, "FPK P7", 'medium', 'slow')
            self.waitAtPlatform()
        else:
            self.shortJourney(True, self.loco.block, "FPK P7", 'medium', dontStop=True)
            # # get a lock on the south link, but if it's not available immediately ...
            # lock = self.loco.getLockNonBlocking(SOUTH)
            # if lock is False:
            #     # stop the train at FPK 7
            #     self.loco.setSpeedSetting('slow')
            #     st = self.getSlowTime("FPK P7") or 8
            #     self.debug("waiting slowtime at FPK P7 " + str(slowTime / 1000))
            #     time.sleep(st)
            #     self.loco.setSpeedSetting(0)
            #     # wait for a lock
            #     lock = self.loco.getLock(SOUTH)

        # # one way or another we have a lock - set the turnouts for FPK 7
        # for r in self.requiredRoutes("FPK P7"):
        #     self.setRoute(r, 0)
        #     # progress to south link
        #     self.shortJourney(True, self.loco.block, "South Link", 'medium', dontStop=True)
        #
        # if self.memory is not None:
        #     m = memories.provideMemory(self.memory)
        #     m.setValue(0)


        self.moveIntoSouthSidings()

        # # select a siding
        # b = None
        # if not self.loco.reversible():
        #     b = self.loco.selectReverseLoop(SOUTH_REVERSE_LOOP)
        # if b is not None:
        #     self.loco.setSpeedSetting('fast')
        #     self.reverseLoop(SOUTH_REVERSE_LOOP)
        #     self.loco.unselectReverseLoop(SOUTH_REVERSE_LOOP)
        #     if lock:
        #         self.unlock(lock)
        # else:
        #     siding = self.loco.selectSiding(SOUTH_SIDINGS)
        #     routes = self.requiredRoutes(siding)
        #     self.shortJourney(True, self.loco.block, siding, 'fast', 'medium', stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        #     self.loco.unselectSiding(siding)
        #
        # self.loco.status = loco.SIDINGS
        return False

class Class47Nth2SthTrack5Nonstop(ClassAnyNth2SthTrack5):
    pass

class ClassA4Nth2SthTrack5Stopping(ClassAnyNth2SthTrack5):
    pass

# loc = loco.Loco(68)
# loc.setBlock(NORTH_REVERSE_LOOP)
# ClassA4Nth2SthTrack5Stopping(loc, None).start()

