import jmri
import util
from jmri_bindings import *
import time
import loco
import track

class ShortJourney(util.Util):
    def __init__(self, loc):
        self.loco = loc
        self.stage = 0
        self.direction = None
        self.startBlock = None
        self.endBlock = None
        self.normalSpeed = None
        self.slowSpeed = None
        self.slowTime = None
        self.stopIRClear = None
        self.routes = []
        self.lock = None
        self.passBlock = False
        self.dontStop = None
        self.endIRSensor = None
        self.lockSensor = None
        self.eStop = False
        self.ignoreOccupiedEndblock = False
        self.lockToUpgrade = None
        self.upgradeLockRoutes = None
        self.sleepTime = None
        self.sleepStart = None
        self.origNormalSpeed = None
        self.setupDone = False
        self.movingWhenStarted = None

    def setup(self, direction=True, startBlock=None, endBlock=None, normalSpeed=None, slowSpeed=None, slowTime=None, unlockOnBlock=False,
                     stopIRClear=None, routes=None, lock=None, passBlock=False, nextBlock=None, dontStop=None, endIRSensor=None,
                     lockSensor=None, eStop=False, ignoreOccupiedEndBlock=False, lockToUpgrade=None, upgradeLockRoutes=None):

        # set variables
        self.direction = direction
        self.startBlock = startBlock
        self.endBlock = endBlock
        self.normalSpeed = normalSpeed
        self.slowSpeed = slowSpeed
        self.slowTime = slowTime
        self.stopIRClear = stopIRClear
        self.routes = routes
        self.lock = lock
        self.passBlock = passBlock
        self.dontStop = dontStop
        self.endIRSensor = endIRSensor
        self.lockSensor = lockSensor
        self.eStop = eStop
        self.ignoreOccupiedEndblock = ignoreOccupiedEndBlock
        self.lockToUpgrade = lockToUpgrade
        self.upgradeLockRoutes = upgradeLockRoutes
        self.unlockSensor = None

        # passBlock implies dontStop
        if self.dontStop is None:
            if self.passBlock is True:
                self.dontStop = True
            else:
                dontStop = False
        if self.dontStop is False and self.passBlock is True:
            raise RuntimeError("dontStop can't be false if passBlock is true")

        # default startblock
        if self.startBlock is None:
            self.startBlock = self.loco.block

        # check we have endblock
        if self.endBlock is None:
            raise RuntimeError("no endblock")

        # convert lockSensor
        if self.lockSensor and type(self.lockSensor) != jmri.Sensor:
            self.lockSensor = sensors.getSensor(lockSensor)

        # convert string speeds to floats
        self.origNormalSpeed = 'dunno'
        if type(self.normalSpeed) == str or type(self.normalSpeed) == unicode:
            self.origNormalSpeed = normalSpeed
            self.normalSpeed = self.loco.speed(self.normalSpeed)
        if type(self.slowSpeed) == str or type(self.slowSpeed) == unicode:
            self.slowSpeed = self.loco.speed(self.slowSpeed)

        # Get a startBlock and endBlock converted to layoutBlocks and get their
        # sensors too.
        self.startBlock, self.startBlockSensor = self.convertToLayoutBlockAndSensor(self.startBlock)
        self.endBlock, self.endBlockSensor = self.convertToLayoutBlockAndSensor(self.endBlock)

        # slowSpeed implies slowTime (if there's no IR sensor involved)
        if self.slowSpeed is not None and self.stopIRClear is None:
            if self.slowTime is None:
                sself.lowTime = self.getSlowtime(self.endBlock.getUserName())

        # convert slowTime to msecs
        if 0 < slowTime < 200:
            self.slowTime = int(slowTime * 1000)


        # if unlockOnBlock is set it means we remove the supplied lock when the block
        # with a matching name moves from ACTIVE to any other state. Get the sensor
        # we need to watch
        if self.unlockOnBlock and self.lock:
            self.unlockSensor = layoutblocks.getLayoutBlock(lock.replace(" lock", "")).getBlock().getSensor()

        self.setupDone = True


    def progress(self):

        # check setup is done
        if not self.setupDone:
            raise RuntimeError('setup not done')

        # check if we're sleeping
        if self.sleepTime:
            if time.time() - self.sleepStart < self.sleepTime:
                # we are still dozing
                return

        if powermanager.getPower() == jmri.Powermanager.OFF:
            # no track power
            return

        if self.stage == 0: # ------------------ startup -----------------------

            # Announce ourselves to the world
            if routes:
                self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName() + " routes: " + ', '.join(routes))
            else:
                self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName() + " routes: None")


            # turn lights on
            self.loco.throttle.setF0(True)

            # are we moving
            if self.loco.throttle.getSpeedSetting() > 0:
                self.startTime = time.time()
                self.movingWhenStarted = True
            else:
                self.movingWhenStarted = False

            # check if we know where we are if the startblock is not occupied
            if self.startBlockSensor.knownState != ACTIVE:
                self.debug("startblock is not occupied")
                if self.knownLocation is None:
                    self.loco.emergencyStop()
                    errstr = str(self.loco.dccAddr) + "start block " + self.startBlock.getUserName() + "is not occupied and no known location"
                    raise RuntimeError(errstr)
                if self.knownLocation != self.startBlock:
                    self.loco.emergencyStop()
                    raise RuntimeError("start block is not occupied and known location does not match start block")

