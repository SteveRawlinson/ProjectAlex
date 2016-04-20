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
        self.shortJourney(True, self.loco.block, "Nth Fast Link", 0.4, routes=routes, lock=lock)

        # slower round the bend
        self.shortJourney(True, self.loco.block, "Nth Fast Inner 1", 0.3)

        # off to the other side of the layout
        self.shortJourney(True, self.loco.block, "Sth Fast Inner 2", 0.5)

        # get a lock on the south link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('South Link Lock')
        if lock is False:
            # stop the train at FPK 7
            self.shortJourney(True, self.loco.block, "FPK P7", 0.3, 0.1, 1000)
            # wait for a lock
            lock = self.getLock('South Link Lock')
        else:
            # we got the lock - set the turnouts for FPK 7
            for r in self.requiredRoutes("FPK P7"):
                self.setRoute(r, 0)
            # progress to FPK 7
            self.shortJourney(True, self.loco.block, "FPK P7", 0.4)
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
        self.shortJourney(True, self.loco.block, siding, 0.3, 0.1, 0, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)
        self.unlock('South Link Lock')

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False

l = loco.Loco(3213)
l.initBlock()
LocoAnyNth2SthTrack1(l).start()

