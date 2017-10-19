import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassFastNth2SthTrack5Nonstop(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory


    # This method should be overridden by the child classes
    def getSpeeds(self):
        return [0.3, 0.2, 0.1]

    def handle(self):
        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the north sidings")

        fullSpeed, bendSpeed, slowSpeed = self.getSpeeds()

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("Nth Fast Inner 1")
        self.shortJourney(True, self.loco.block, "Nth Fast Link", fullSpeed, routes=routes, lock=lock)

        # slower round the bend
        self.shortJourney(True, self.loco.block, "Nth Fast Inner 1", bendSpeed)

        # off to the other side of the layout
        self.shortJourney(True, self.loco.block, "Sth Fast Inner 2", fullSpeed)

        # get a lock on the south link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('South Link Lock')
        if lock is False:
            # stop the train at FPK 7
            self.shortJourney(True, self.loco.block, "FPK P7", fullSpeed, slowSpeed, 1000)
            # wait for a lock
            lock = self.getLock('South Link Lock')
        else:
            # we got the lock - set the turnouts for FPK 7
            for r in self.requiredRoutes("FPK P7"):
                self.setRoute(r, 0)
            # progress to FPK 7
            self.shortJourney(True, self.loco.block, "FPK P7", fullSpeed, dontStop=True)
            # check we still have the lock
            rc = self.checkLock(lock)
            if rc is False :
                # we lost it, abort!
                self.throttle.setSpeedSetting(0)
                print loco, "race conditions on South Link Lock?"
                return False

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        routes = self.requiredRoutes(siding)
        self.shortJourney(True, self.loco.block, siding, 0.3, 0.2, 0, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        self.unlock('South Link Lock')

        self.loco.status = loco.SIDINGS
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        return False

loc = loco.Loco(3213)
loc.setBlock("Nth Sidings 2")
ClassFastNth2SthTrack5Nonstop(loc, None).start()