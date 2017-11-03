import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassFreightNth2SthTrack1Nonstop(alex.Alex):
    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory
        self.knownLocation = None

    def getSpeeds(self):
        return CLASS_47_SPEEDS

    def handle(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we're in the right place for this journey
        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we are facing the right way
        if not self.reversible() and self.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        fast, medium, slow = self.getSpeeds()

        self.loco.status = loco.MOVING

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        if self.loco.inReverseLoop():
            routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('PAL P1')
        else:
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", fast, routes=routes, lock=lock, dontStop=True)

        # on to PAL P1
        self.shortJourney(True, self.loco.block, "PAL P1", medium, dontStop=True)

        # NSG to AAP
        self.shortJourney(True, "PAL P1", "AAP P4", medium, dontStop=True)

        # AAP to FPK
        self.shortJourney(True, "AAP P4", "FPK P1", medium, dontStop=True)

        # get a lock and don't block
        lock = self.getLockNonBlocking("South Link Lock")
        if lock is False:
            # wait here for a bit
            self.loco.setSpeedSetting(slow)
            time.sleep(1)
            self.loco.setSpeedSetting(0)
            # get a lock
            lock = self.getLock('South Link Lock')
            # off we go
            self.loco.setSpeedSetting(slow)

        # remove the memory - this is how the calling process knows we are done with the track
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        # see if the reverse loop is free
        b = self.loco.selectReverseLoop(SOUTH_REVERSE_LOOP)
        if b is not None:
            self.setRoute("Sth Hertford Inner")
            self.loco.setSpeedSetting(medium)
            self.reverseLoop(SOUTH_REVERSE_LOOP)
            self.loco.unselectReverseLoop(SOUTH_REVERSE_LOOP)
        else:
            # select a siding
            siding = self.loco.selectSiding(SOUTH_SIDINGS)
            if siding.getId() == "FP sidings":
                routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
                self.shortJourney(True, self.loco.block, siding, medium, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            else:
                routes = self.requiredRoutes(self.loco.block)
                self.shortJourney(True, self.loco.block, "South Link", medium, routes=routes)
                routes = self.requiredRoutes(siding)
                self.shortJourney(True, self.loco.block, siding, fast, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            self.loco.unselectSiding(siding)
            self.loco.wrongway = True


        self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False
