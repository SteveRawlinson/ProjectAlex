import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassA4Nth2SthTrack3Stopping(alex.Alex):

    def go(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we're in the right place for this journey
        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        # # get a 'lock' on the north link track
        # lock = self.getLock('North Link Lock')
        #
        # # Out the nth sidings
        # if self.loco.inReverseLoop():
        #     routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('NSG P1')
        # else:
        #     routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("NSG P1")
        # self.shortJourney(True, self.loco.block, "Nth Fast Link", 0.6, routes=routes, dontStop=True)
        #
        # # on to NSG P1
        # self.shortJourney(True, self.loco.block, "NSG P1", 0.5, dontStop=True, lock=lock)

        self.leaveNorthSidings('NSG P1', stop=False)

        # NSG to AAP
        self.shortJourney(True, "NSG P1", "AAP P2", 'medium', dontStop=True)

        # AAP to FPK
        self.shortJourney(True, "AAP P2", "FPK P3", 'medium', 'slow', 14000)
        self.waitAtPlatform()

        # # FPK to Sth Sidings
        # lock = self.getLock('South Link Lock')
        #
        # # see if the reverse loop is free
        # b = self.loco.selectReverseLoop(SOUTH_REVERSE_LOOP)
        # if b is not None:
        #     self.setRoute("Sth Welwyn Inner")
        #     self.loco.setSpeedSetting(0.5)
        #     self.reverseLoop(SOUTH_REVERSE_LOOP)
        #     self.loco.unselectReverseLoop(SOUTH_REVERSE_LOOP)
        # else:
        #     # select a siding
        #     siding = self.loco.selectSiding(SOUTH_SIDINGS)
        #     if siding.getId() == "FP sidings":
        #         routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
        #         self.shortJourney(True, self.loco.block, siding, 0.4, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        #     else:
        #         routes = self.requiredRoutes(self.loco.block)
        #         self.shortJourney(True, self.loco.block, "South Link", 0.4, routes=routes)
        #         routes = self.requiredRoutes(siding)
        #         self.shortJourney(True, self.loco.block, siding, 0.6, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        #     self.loco.unselectSiding(siding)
        #     self.loco.wrongway = True

        self.moveIntoSouthSidings()

        self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False
