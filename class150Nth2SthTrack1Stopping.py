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


class Class150Nth2SthTrack1Stopping(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory


    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        self.loco.status = loco.MOVING

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", 0.6, routes=routes, lock=lock)
        self.unlock('North Link Lock') # is done anyway by shortJourney but the makes it more readable

        # on to PAL P1
        self.shortJourney(True, self.loco.block, "PAL P1", 0.4, slowSpeed=0.2, slowTime=6000)
        self.waitAtPlatform()

        # PAL to AAP
        self.shortJourney(True, "PAL P1", "AAP P4", 0.4, 0.2, 5000)
        self.waitAtPlatform()

        # AAP to FPK
        self.shortJourney(True, "AAP P4", "FPK P1", 0.4, 0.25, 11000)
        self.waitAtPlatform()

        # FPK to Sth Sidings
        lock = self.getLock('South Link Lock')

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        if siding.getId() == "FP sidings":
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.4, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        else:
            routes = self.requiredRoutes(self.loco.block)
            self.shortJourney(True, self.loco.block, "South Link", 0.4, routes=routes)
            routes = self.requiredRoutes(siding)
            self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False


