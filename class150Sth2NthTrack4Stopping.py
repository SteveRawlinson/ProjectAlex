import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class Class150Sth2NthTrack4Stopping(alex.Alex):


    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        fast, medium, slow = 'fast', 'medium', 'slow'

        self.loco.status = loco.MOVING
        start = time.time()

        self.leaveSouthSidings('FPK P4')

        # # out of sth sidings to FPK
        # lock = self.getLock('South Link Lock')
        # routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes('FPK P4')
        # self.shortJourney(False, self.loco.block, "FPK P4", medium, slowSpeed=slow, routes=routes, lock=lock)
        # self.waitAtPlatform()

        # FPK to AAP
        self.shortJourney(False, self.loco.block, "AAP P1", medium, slowSpeed=slow)
        self.waitAtPlatform()

        # AAP to PAL
        self.shortJourney(False, self.loco.block, "NSG P2", medium, slowSpeed=slow)
        self.waitAtPlatform()

        self.moveIntoNorthSidings()

        # if self.getJackStatus() == NORMAL and self.loco.rarity() == 0:
        #     # If this loco has a rarity of zero and we're not shutting down operations
        #     # there's no point in going all the way to the sidings because we'll just get
        #     # started up again. Stop on the North Link
        #     self.debug("stopping early")
        #     routes = self.requiredRoutes(self.loco.block)
        #     self.shortJourney(False, self.loco.block, "North Link", medium, slowSpeed=slow, routes=routes)
        #     # check JackStatus hasn't changed in the meantime
        #     if self.getJackStatus() == STOPPING:
        #         self.debug("JackStatus is now STOPPING - moving to siding")
        #         siding = self.loco.selectSiding(NORTH_SIDINGS)
        #         routes = self.requiredRoutes(siding)
        #         self.shortJourney(False, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        # else:
        #     # PAL to North sidings
        #     self.debug("not stopping early. status :" + str(self.getJackStatus()) + " doesn't equal normal: " + str(NORMAL) + " self.rarity(): " + str(self.loco.rarity()))
        #     siding = self.loco.selectSiding(NORTH_SIDINGS)
        #     routes = self.requiredRoutes(self.loco.block)
        #     self.shortJourney(False, self.loco.block, "North Link", medium, routes=routes, lock=lock)
        #     routes = self.requiredRoutes(siding)
        #     self.shortJourney(False, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        stop = time.time()
        print self.loco.dccAddr, "route completed in", stop - start, 'seconds'


        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False

class Loco1087Sth2NthTrack4Stopping(Class150Sth2NthTrack4Stopping):
    pass
