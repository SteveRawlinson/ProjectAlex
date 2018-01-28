import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassFastSth2NthTrack6Nonstop(alex.Alex):
        
    def go(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        fullSpeed, bendSpeed, slowSpeed = 'fast', 'bend', 'slow'

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        self.leaveSouthSidings('FPK P8', stop=False)

        # All the way to North Fast Outer 2
        self.shortJourney(False, self.loco.block, "Nth Fast Outer 2", fullSpeed, dontStop=True)

        # get a lock on the north link, but if it's not available immediately we need to know pronto
        lock = self.loco.getLockNonBlocking(NORTH)
        if lock.empty():
            # stop the train at North Fast Outer 1
            sp = self.loco.speed("north fast outer 1 halting", 'medium')
            self.shortJourney(False, self.loco.block, "Nth Fast Outer 1", sp, 'slow')
            # wait for a lock
            lock = self.loco.getLock(NORTH)

        self.moveIntoNorthSidings(lock)

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

# TGV
class Loco4404Sth2NthTrack6Nonstop(ClassFastSth2NthTrack6Nonstop):
    pass


