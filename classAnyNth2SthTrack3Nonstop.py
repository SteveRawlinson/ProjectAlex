import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *


class ClassAnyNth2SthTrack3Nonstop(alex.Alex):


    def go(self):
        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        # check we're in the right place for this journey
        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        # check we are facing the right way
        if not self.loco.reversible() and self.loco.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING


        speed = self.loco.getSpeed('fast going slow', 'medium')
        self.leaveNorthSidings('NSG P1', speed=speed)



        # NSG to AAP
        self.shortJourney(True, self.loco.block, "AAP P2", speed, dontStop=True)

        # AAP to FPK
        self.shortJourney(True, self.loco.block, "FPK P3", speed, dontStop=True)

        self.moveIntoSouthSidings(speed=speed)


        return False

class Class47Nth2SthTrack3Nonstop(ClassAnyNth2SthTrack3Nonstop):
    pass

class Loco1124Nth2SthTrack3Nonstop(ClassAnyNth2SthTrack3Nonstop):
    pass

        # loc = loco.Loco(7405)
# loc.setBlock(NORTH_REVERSE_LOOP)
# Class47Nth2SthTrack3Nonstop(loc, None).start()