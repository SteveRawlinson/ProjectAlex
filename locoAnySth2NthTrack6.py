import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class LocoAnySth2NthTrack6(alex.Alex):
        
    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the south link track
        lock = self.getLock('South Link Lock')

        # Out the sth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("FPK P8")
        self.shortJourney(False, self.loco.block, "South Link", 0.2, routes=routes, lock=lock, passBlock=True)

        # All the way to North Fast Outer 1
        self.shortJourney(False, self.loco.block, "Nth Fast Outer 2", 0.4)

        # slow down a bit
        # self.throttle.setSpeedSetting(0.5)

        # get a lock on the north link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('North Link Lock')
        if lock is False:
            # stop the train at North Fast Outer 1
            self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", 0.3, 0.1, 1000)
            # wait for a lock
            lock = self.getLock('North Link Lock')
        else:
            # we got the lock - set the turnouts for Nth Fast Outer 1
            for r in self.requiredRoutes("Nth Fast Outer 1"):
                self.setRoute(r, 0)
            # progress to ...
            self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", 0.4, passBlock=True)
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
        self.shortJourney(False, self.loco.block, siding, 0.2, 0.2, 0, stopIRClear=IRSENSORS[siding.getID()], routes=routes, lock=lock)

        print "route complete."
        stop = time.time()
        print "route took", stop - start, 'seconds'
        self.loco.status = loco.SIDINGS

        return False

l = loco.Loco(3213)
l.initBlock()
LocoAnySth2NthTrack6(l).start()

