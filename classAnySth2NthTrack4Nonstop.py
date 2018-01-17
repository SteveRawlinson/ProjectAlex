import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnySth2NthTrack4Nonstop(alex.Alex):

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we are facing the right way
        if not self.loco.reversible() and self.loco.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING

        speed = self.loco.getSpeed('fast going slow', 'medium')
        self.leaveSouthSidings('FPK P4', stop=False, speed=speed)

        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P1", speed, dontStop=True)

        # AAP to PAL
        self.shortJourney(True, self.loco.block, "NSG P2", speed, dontStop=True)

        self.moveIntoNorthSidings(speed=speed)

        return False

class Class47Sth2NthTrack4Nonstop(ClassAnySth2NthTrack4Nonstop):
    pass

class Loco1124Sth2NthTrack4Nonstop(ClassAnySth2NthTrack4Nonstop):
    pass

        # loc = loco.Loco(7405)
# loc.setBlock(SOUTH_REVERSE_LOOP)
# Class47Sth2NthTrack4Nonstop(loc, None).start()