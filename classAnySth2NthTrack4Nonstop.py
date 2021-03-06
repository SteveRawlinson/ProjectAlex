import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnySth2NthTrack4Nonstop(alex.Alex):

    def go(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we are facing the right way
        if not self.loco.reversible() and self.loco.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        if self.loco.reversible():
            direction = False
        else:
            direction = True

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        speed = self.loco.getSpeed('fast going slow', 'medium')
        self.leaveSouthSidings('FPK P4', stop=False, speed=speed)

        # FPK to AAP
        self.shortJourney(direction, self.loco.block, "AAP P1", speed, dontStop=True)

        if self.loco.fast():
            # we need to do some jiggery pokery here because NSG doesn't get
            # 'occupied' until the engine (at the back) goes into the block
            loc = self.loco.getLockNonBlocking(NORTH)
            if loc.empty():
                loc.getLockOrStopLoco(speed='fast going slow', slowtime=12)
                self.setRoute(self.loco.track.exitRoute())
                time.sleep(3)
                b, s = self.convertToLayoutBlockAndSensor("NSG P2")
                if s.getKnownState() == ACTIVE:
                    self.loco.setBlock(b)
                else:
                    self.shortJourney(direction, self.loco.block, "NSG P2", speed, dontStop=True)
            else:
                self.setRoute(self.loco.track.exitRoute())
                # AAP to NSG
                self.shortJourney(direction, self.loco.block, "NSG P2", speed, dontStop=True)
        else:
            loc = None
            self.shortJourney(direction, self.loco.block, "NSG P2", speed, dontStop=True)

        self.moveIntoNorthSidings(speed=speed, lock=loc)

        return False

class Class47Sth2NthTrack4Nonstop(ClassAnySth2NthTrack4Nonstop):
    pass

class Loco3314Sth2NthTrack4Nonstop(ClassAnySth2NthTrack4Nonstop):
    pass

