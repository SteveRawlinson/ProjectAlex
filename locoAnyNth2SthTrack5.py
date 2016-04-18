import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class LocoAnyNth2SthTrack1(alex.Alex):
        
    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("Nth Fast Inner 1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", 0.6, routes=routes, lock=lock)

        # All the way to FPK P7
        self.shortJourney(True, self.loco.block, "FPK P7", 0.6)

        # get a lock on the south link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('South Link Lock', loco)
        if lock is False:
            # stop the train
            self.gradualHalt(2)
            # wait for a lock
            lock = self.getLock('South Link Lock')
        else:
            # we got a lock
            self.waitMsec(250)
            # check we still have it
            rc = self.checkLock(lock, loco)
            if rc is False :
                # we lost it, abort!
                self.throttle.setSpeedSetting(0)
                print loco, "race conditions on South Link Lock?"
                return False

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
        self.shortJourney(True, self.loco.block, siding, 0.5, 0.2, 0, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)
        self.unlock('South Link Lock')

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False

# l = loco.Loco(2144)
# l.initBlock()
# Loco2144Nth2SthTrack(l).start()
