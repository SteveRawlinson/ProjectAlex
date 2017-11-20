import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassAnyNth2SthTrack1Nonstop(alex.Alex):
    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory
        self.knownLocation = None


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

        self.loco.status = loco.MOVING

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        if self.loco.inReverseLoop():
            routes = [self.requiredRoutes(self.loco.block)[1]] + self.requiredRoutes('PAL P1')
        else:
            routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        self.shortJourney(True, self.loco.block, "Nth Slow Link", self.loco.speed('fast'), routes=routes, lock=lock, dontStop=True)

        # on to PAL P1
        self.shortJourney(True, self.loco.block, "PAL P1", self.loco.speed('medium'), dontStop=True)

        # NSG to AAP
        self.shortJourney(True, "PAL P1", "AAP P4", self.loco.speed('medium'), dontStop=True)

        # AAP to FPK
        lock = self.getLockNonBlocking("North Link")
        if lock is None:
            self.shortJourney(True, "AAP P4", "FPK P1", self.loco.speed('medium'), self.loco.speed('slow'), 16000)
            self.waitAtPlatform()
            lock = self.getLock('South Link Lock')
        else:
            self.shortJourney(True, "AAP P4", "FPK P1", self.loco.speed('medium'), dontStop=True)


        # see if the reverse loop is free
        b = self.loco.selectReverseLoop(SOUTH_REVERSE_LOOP)
        if b is not None:
            self.setRoute("Sth Hertford Inner")
            self.loco.setSpeedSetting(0.5)
            self.reverseLoop(SOUTH_REVERSE_LOOP)
            self.loco.unselectReverseLoop(SOUTH_REVERSE_LOOP)
        else:
            # select a siding
            siding = self.loco.selectSiding(SOUTH_SIDINGS)
            if siding.getId() == "FP sidings":
                routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes(siding)
                self.shortJourney(True, self.loco.block, siding, self.loco.speed('medium'), stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            else:
                routes = self.requiredRoutes(self.loco.block)
                self.shortJourney(True, self.loco.block, "South Link", self.loco.speed('medium'), routes=routes)
                routes = self.requiredRoutes(siding)
                self.shortJourney(True, self.loco.block, siding, self.loco.speed('fast'), stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            self.loco.unselectSiding(siding)
            if self.loco.reversible() is False:
                self.loco.wrongway = True

        # remove the memory - this is how the calling process knows we are done
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        self.loco.status = loco.SIDINGS

        self.debug(type(self).__name__ + ' finished')

        return False

class Class47Nth2SthTrack1Nonstop(ClassAnyNth2SthTrack1Nonstop):
    pass