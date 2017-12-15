import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Nth2SthTrack1Stopping(alex.Alex):

    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        fast, medium, slow = 'fast', 'medium', 'slow'


        # Out the nth sidings
        # routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        # self.shortJourney(True, self.loco.block, "Nth Slow Link", fast, routes=routes)
        #
        # # on to PAL P1
        # dest = "PAL P1"
        # self.shortJourney(True, self.loco.block, dest, medium, slowSpeed=slow, lock=lock)
        # self.waitAtPlatform()

        self.leaveNorthSidings('PAL P1')

        # PAL to AAP
        dest = "AAP P4"
        self.shortJourney(True, self.loco.block, dest, medium, slowSpeed=slow)
        self.waitAtPlatform()

        # AAP to FPK
        dest = "FPK P1"
        self.shortJourney(True, "AAP P4", dest, medium, slowSpeed=slow)
        self.waitAtPlatform()

        self.moveIntoSouthSidings()

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

        self.debug(type(self).__name__ + ' finished')

        return False

# loc = loco.Loco(5144)
# loc.setBlock("Nth Sidings 3")
# Class150Nth2SthTrack1Stopping(loc, None).start()


class Loco1087Nth2SthTrack1Stopping(Class150Nth2SthTrack1Stopping):
    pass



# class Loco1234Nth2SthTrack1Stopping(class150Nth2SthTrack1Stopping):
#     def getSpeeds(self):
#         return [0.5, 0.4, 0.3]
#     def getSlowTimes(self):
#         return {"PAL P1": 8, "AAP P4": 7, "FPK P1": 15 }
