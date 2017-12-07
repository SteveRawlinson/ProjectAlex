import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Nth2SthTrack3Stopping(alex.Alex):


    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we're in the right place for this journey
        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        fast, medium, slow = 'fast', 'medium', 'slow'

        self.loco.status = loco.MOVING

        # # get a 'lock' on the north link track
        # lock = self.getLock('North Link Lock')
        #
        # # Out the nth sidings
        # routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("NSG P1")
        # self.shortJourney(True, self.loco.block, "Nth Fast Link", fast, routes=routes)
        #
        # # on to NSG P1
        # self.shortJourney(True, self.loco.block, "NSG P1", medium, slowSpeed=slow, lock=lock)
        # self.waitAtPlatform()

        self.leaveNorthSidings('NSG P1')

        # PAL to AAP
        self.shortJourney(True, "NSG P1", "AAP P2", medium, slowSpeed=slow)
        self.waitAtPlatform()

        # AAP to FPK
        self.shortJourney(True, "AAP P2", "FPK P3", medium, slowSpeed=slow)
        self.waitAtPlatform()

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.moveIntoSouthSidings(lock)

        # # select a siding
        # siding = self.loco.selectSiding(SOUTH_SIDINGS)
        # if siding.getId() == "FP sidings":
        #     routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
        #     self.shortJourney(True, self.loco.block, siding, medium, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        # else:
        #     routes = self.requiredRoutes(self.loco.block)
        #     self.shortJourney(True, self.loco.block, "South Link", medium, routes=routes)
        #     routes = self.requiredRoutes(siding)
        #     self.shortJourney(True, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        # self.loco.unselectSiding(siding)
        #
        #
        # self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False

class Loco1087Nth2SthTrack3Stopping(Class150Nth2SthTrack3Stopping):
    pass

