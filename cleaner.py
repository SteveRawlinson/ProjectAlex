import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

# alex.sensors = sensors  # explicitly add to auto namespace
# alex.memories = memories
# alex.routes = routes
# alex.layoutblocks = layoutblocks
# alex.ACTIVE = ACTIVE


class Cleaner(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory


    def handle(self):
        self.getLocoThrottle(self.loco)
        self.loco.emergencyStop()
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        self.loco.status = loco.MOVING

        start = time.time()
        platformWaitTimeMsecs = self.platformWaitTimeMsecs
        addr = self.loco.dccAddr



loc = loco.Loco(7405)
Cleaner(loc, mem).start()