import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnySth2NthTrack2Nonstop(alex.Alex):

    def go(self):

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

        speed = self.loco.getSpeed('fast going slow', 'medium')
        self.leaveSouthSidings("FPK P2", speed=speed)



        # FPK to AAP
        self.shortJourney(True, self.loco.block, "AAP P3", speed, dontStop=True)

        if self.loco.fast():
            # we need to do some jiggery pokery here because NSG doesn't get
            # 'occupied' until the engine (at the back) goes into the block
            loc = self.loco.getLockNonBlocking(NORTH)
            if loc.empty():
                loc.getLockOrStopLoco(speed='fast going slow', slowtime=12)
                self.setRoute(self.loco.track.exitRoute())
                time.sleep(3)
                b, s = self.convertToLayoutBlockAndSensor("PAL P2")
                if s.getKnownState() == ACTIVE:
                    self.loco.setBlock(b)
                else:
                    self.shortJourney(direction, self.loco.block, "PAL P2", speed, dontStop=True)
            else:
                self.setRoute(self.loco.track.exitRoute())
                # AAP to NSG
                self.shortJourney(direction, self.loco.block, "PAL P2", speed, dontStop=True)
        else:
            loc = None
            self.shortJourney(direction, self.loco.block, "PAL P2", speed, dontStop=True)

        self.moveIntoNorthSidings(speed=speed, lock=loc)


        return False

class Class47Sth2NthTrack2Nonstop(ClassAnySth2NthTrack2Nonstop):
    pass

class Loco1124Sth2NthTrack2Nonstop(ClassAnySth2NthTrack2Nonstop):
    pass

        # loc = loco.Loco(7405)
# loc.setBlock(SOUTH_REVERSE_LOOP)
# Class47Sth2NthTrack2Nonstop(loc, None, None).start()