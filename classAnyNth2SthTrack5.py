import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnyNth2SthTrack5(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory

    def handle(self):
        if not self.loco.northSidings():
            raise RuntimeError("I'm not in the north sidings")



        # check we have a throttle
        if self.loco.throttle is None:
            self.getLocoThrottle(self.loco)

        self.loco.status = loco.MOVING
        start = time.time()

        # get a 'lock' on the north link track
        lock = self.getLock('North Link Lock')

        # Out the nth sidings
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("Nth Fast Inner 1")
        sp = self.loco.speed('northSidings') or self.loco('fast')
        self.shortJourney(True, self.loco.block, "North Link", sp, routes=routes, dontStop=True)
        self.shortJourney(True, self.loco.block, "Nth Fast Link", 'fast')

        # slower round the bend
        self.shortJourney(True, self.loco.block, "Nth Fast Inner 1", 'northFastBend', lock=lock)

        # off to the other side of the layout
        self.shortJourney(True, self.loco.block, "Sth Fast Inner 2", 'medium')

        self.shortJourney(True, self.loco.block, "FPK 7", 'medium')

        # get a lock on the south link, but if it's not available immediately ...
        lock = self.getLockNonBlocking('South Link Lock')
        if lock is False:
            # stop the train at FPK 7
            self.loco.setSpeedSetting('slow')
            time.sleep(8)
            self.loco.setSpeedSetting(0)
            # wait for a lock
            lock = self.getLock('South Link Lock')

        # we got the lock - set the turnouts for FPK 7
        for r in self.requiredRoutes("FPK P7"):
            self.setRoute(r, 0)
            # progress to south link
            self.shortJourney(True, self.loco.block, "South Link", 'medium', dontStop=True)

        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)

        # select a siding
        siding = self.loco.selectSiding(SOUTH_SIDINGS)
        routes = self.requiredRoutes(siding)
        self.shortJourney(True, self.loco.block, siding, 'fast', 'medium', stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)

        self.loco.status = loco.SIDINGS
        return False

