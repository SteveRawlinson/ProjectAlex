import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnySth2NthTrack2Nonstop(alex.Alex):

    def handle(self):

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        if not self.loco.southSidings():
            raise RuntimeError("I'm not in the south sidings!")

        # check we are facing the right way
        if not self.loco.reversible() and self.loco.wrongway:
            raise RuntimeError(self.loco.nameAndAddress() + " is facing the wrong way")

        medium = self.loco.speed('medium')

        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        # check we have a track
        if self.track is None:
            self.tracks = []
            self.initTracks()
            self.track = self.tracks[1]


        self.loco.status = loco.MOVING

        self.leaveSouthSidings("FPK P2")

        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P3", medium, dontStop=True)

        # AAP to PAL
        self.shortJourney(True, self.loco.block, "PAL P2", medium, dontStop=True)

        # see if we can get a lock but don't wait for one
        lock = self.loco.getLockNonBlocking(NORTH)
        if lock.empty():
            # we didn't get a lock, stop at the signal
            self.loco.graduallyChangeSpeed('slow')
            time.sleep(self.getSlowtime("PAL P2"))
            self.loco.setSpeedSetting(0)

        # one way or another we now have the lock
        # self.shortJourney(True, self.loco.block, 'North Link', medium, routes=routes, dontStop=True)


        self.moveIntoNorthSidings()

        self.loco.status = loco.SIDINGS
        self.debug(type(self).__name__ + ' finished')
        return False

class Class47Sth2NthTrack2Nonstop(ClassAnySth2NthTrack2Nonstop):
    pass

class Loco1124Sth2NthTrack2Nonstop(ClassAnySth2NthTrack2Nonstop):
    pass

        # loc = loco.Loco(7405)
# loc.setBlock(SOUTH_REVERSE_LOOP)
# Class47Sth2NthTrack2Nonstop(loc, None, None).start()