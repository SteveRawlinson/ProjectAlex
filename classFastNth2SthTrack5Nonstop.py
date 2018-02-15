import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassFastNth2SthTrack5Nonstop(alex.Alex):

    def go(self):
        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the north sidings")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        fullSpeed, bendSpeed, slowSpeed = 'fast', 'bend', 'slow'

        self.loco.status = loco.MOVING

        self.leaveNorthSidings("Nth Fast Inner 1")

        # off to the other side of the layout
        self.shortJourney(True, self.loco.block, "Sth Fast Inner 2", fullSpeed, dontStop=True)

        # get a lock on the North link, but if it's not available immediately we need to know pronto
        lock = self.loco.getLockNonBlocking(SOUTH)
        if lock.empty():
            # slow down till we get to FPK P7
            self.shortJourney(True, self.loco.block, "FPK P7", 'medium', dontStop=True)
            # try to get the lock again
            lock = self.loco.getLockNonBlocking(SOUTH)
            if lock.empty():
                # stop the train at FPK 7 unless we get a lock before slowtime runs out
                lock.getLockOrStopLoco("FPK P7")
        else:
            routes = self.requiredRoutes("FPK P7")
            if lock.partial():
                sp = self.loco.speed('off track south partial lock', 'fast')
                moreRoutes = ["Back Passage"]
            else:
                moreRoutes = None
                sp = fullSpeed
            self.shortJourney(True, endBlock="FPK P7", normalSpeed=sp, dontStop=True, routes=routes, lockToUpgrade=lock, upgradeLockRoutes=moreRoutes)

        self.moveIntoSouthSidings(lock)

        return False

# Javelin
class Loco5004Nth2SthTrack5Nonstop(ClassFastNth2SthTrack5Nonstop):
    pass

# Eurostar
class Loco3213Nth2SthTrack5Nonstop(ClassFastNth2SthTrack5Nonstop):
    pass

# Ave Talgo
class Loco6719Nth2SthTrack5Nonstop(ClassFastNth2SthTrack5Nonstop):
    pass

# Class 91
class Loco1124Nth2SthTrack5Nonstop(ClassFastNth2SthTrack5Nonstop):
    pass

# TGV
class Loco4404Nth2SthTrack5Nonstop(ClassFastNth2SthTrack5Nonstop):
    pass

