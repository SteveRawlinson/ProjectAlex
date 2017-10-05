import jmri
import time
import random
import os
from jmri_bindings import *
from myroutes import ROUTEMAP

DEBUG = True

# statuses
NORMAL = 0
STOPPING = 1
ESTOP = 2

# The Alex class provides a series of utility methods which can be used
# to control a locomotive around a layout. It is intended to be used as
# a parent to a particular journey class

# noinspection PyInterpreter
class Alex(jmri.jmrit.automat.AbstractAutomaton):

    # init() is called exactly once at the beginning to do
    # any necessary configuration.
    def init(self):
        self.sensorStates = None
        self.platformWaitTimeMsecs = 10000
        return

    def debug(self, message):
        if DEBUG:
            print 'alex: ' + str(self.loco.dccAddr) + ': ' + message

    # Get's a 'lock' on a memory variable. It sets the variable
    # to the loco number but only if the value is blank. If 
    # it's already got a value then we wait for a while to see
    # if it clears, otherwise we give up.
    def getLock(self, mem, loco=None):
        if loco is None:
            loco = self.loco
        lock = False
        tries = 0
        while lock is not True:
            print loco.dccAddr, "getting lock on", mem
            value = memories.getMemory(mem).getValue()
            if value == str(loco.dccAddr):
                self.debug("already had a lock, returning")
                return mem
            if value is None or value == '':
                memories.getMemory(mem).setValue(str(loco.dccAddr))
                time.sleep(1)
                value = memories.getMemory(mem).getValue()
                if value == str(loco.dccAddr):
                    self.debug("lock acquired")
                    lock = True
                else:
                    # race condition and we lost
                    tries += 1
                    if tries < 20:
                        print loco.dccAddr, "new memory setting did not stick, trying again"
                        time.sleep(5)
                    else:
                        print loco.dccAddr, "giving op on lock"
                        raise RuntimeError(str(loco.dccAddr) + ": giving up getting lock on " + mem)
            else:
                # link track is busy
                tries += 1
                if tries < 40:
                    print loco.dccAddr, "track is locked, waiting ..."
                    time.sleep(5)
                else:
                    print loco.dccAddr, "giving up on lock"
                    raise RuntimeError(str(loco.dccAddr) + ": giving up getting lock on " + mem)
        return mem

    # Attempts to get a lock and returns immediately whether or
    # not the attempt was successful. No race condition testing
    # is done, the calling function can do that with checkLock()
    def getLockNonBlocking(self, mem, loco = None):
        if loco is None:
            loco = self.loco
        lock = False
        print loco.dccAddr, "getting non-blocking lock on", mem
        value = memories.getMemory(mem).getValue()
        if value == str(loco.dccAddr):
            return mem
        if value is None or value == '':
            memories.getMemory(mem).setValue(str(loco.dccAddr))
            return mem
        print loco.dccAddr, "failed to get non-blocking lock on", mem
        return False

    # Returns true if the loco supplied has a lock on the
    # mem supplied, false otherwise
    def checkLock(self, mem, loco=None):
        if loco is None:
            loco = self.loco
        memory = memories.getMemory(mem)
        if memory is None:
            memory = memories.newMemory(mem)
        if memory is None:
            print loco.dccAddr, "could not create memory called", mem, "giving up"
            raise RuntimeError('coulnd not create new memory')
        if memory and memory.getValue() == str(loco.dccAddr):
            return True
        print loco.dccAddr, "does not have lock on ", mem
        return False

    # sets (triggers) a route
    def setRoute(self, route, sleeptime=2):
        print self.loco.dccAddr, 'setting route', route
        r = routes.getRoute(route)
        if r is None:
            raise RuntimeError("no such route: " + route)
        r.activateRoute()
        r.setRoute()
        if sleeptime is not None and sleeptime > 0:
            time.sleep(sleeptime)

    # removes a lock
    def unlock(self, mem, loco=None):
        # if there's no lock silently return
        if memories.getMemory(mem).getValue() is None or memories.getMemory(mem).getValue() == "":
            return
        if loco is None:
            loco = self.loco
        self.debug('unlocking ' + mem)
        if memories.getMemory(mem).getValue() != str(loco.dccAddr):
            raise RuntimeError("loco " + str(loco.dccAddr) + " attempted to remove lock it does not own on mem " + mem)
        memories.getMemory(mem).setValue(None)

    # Calculates the routes required to connect the siding using
    # a dictionary (aka hash) specified in an external file
    def requiredRoutes(self, siding):
        if siding is None:
            raise RuntimeError("siding cannot be None")
        if type(siding) == jmri.Block:
            siding = siding.getUserName()
        elif type(siding) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            siding = siding.getId()
        if siding in ROUTEMAP:
            return ROUTEMAP[siding]
        return [siding]


    def emergencyStop(self):
        self.throttle.setSpeedSetting(-1)
        self.waitMsec(250)
        self.throttle.setSpeedSetting(-1)

    # Brings the locomotive controlled by the supplied throttle
    # to a gradual halt by reducing the speed setting over time seconds
    def gradualHalt(self, time=5, granularity=1):
        if time <= granularity:
            print self.loco.dccAddr, "stopping train"
            self.throttle.setSpeedSetting(0)
            self.waitMsec(250)
            self.throttle.setSpeedSetting(0)
            return
        if granularity < 0.25:
            granularity = 0.25 # avoid too many loconet messages
        print self.loco.dccAddr, "bringing train to halt over", time, "secs"
        speed = self.throttle.getSpeedSetting()
        times = time / granularity
        speedDiff = speed / times
        print self.loco.dccAddr, "speed:", speed, "times:", times, "speedDiff:", speedDiff
        while True:
            speed = self.throttle.getSpeedSetting()
            newSpeed = speed - speedDiff
            if newSpeed < 0:
                newSpeed = 0
            print "    gradual halt setting speed", newSpeed
            self.throttle.setSpeedSetting(newSpeed)
            if newSpeed == 0:
                return

    # Acts differently on alternate calls. On calls 0, 2, 4 ...
    # it records the state of a list of sensors. On calls 1, 3 ...
    # it returns a list of sensors which have changed state since
    # the previous call.
    #
    # The intended use is to call this method twice with the same
    # list of sensors, once just before a call to waitChange() and
    # one after, to determine which sensor(s) has changed.
    def changedSensors(self, sensorList):
        if self.sensorStates is None:
            self.sensorStates = []
            for s in sensorList:
                self.sensorStates.append(s.getState())
            return
        changedList = []
        for i in range(len(sensorList)):
            if sensorList[i].getState() != self.sensorStates[i]:
                changedList.append(sensorList[i])
        self.sensorStates = None
        return changedList

    def platformMessage(self):
        print self.loco.dccAddr, "waiting at platform for ", self.platformWaitTimeMsecs / 1000, "secs"

    def waitAtPlatform(self):
        self.platformMessage()
        waitTimeMsecs = self.platformWaitTimeMsecs + random(0, self.platformWaitTimeMsecs / 2)
        self.waitMsec(waitTimeMsecs)

    # Gets a DCC throttle for the loco supplied
    def getLocoThrottle(self, loc):
        throttleAttempts = 0
        while throttleAttempts < 2 and loc.throttle is None:
            time.sleep(5)
            loc.throttle = self.getThrottle(loc.dccAddr, loc.longAddr)
            throttleAttempts += 1
        if loc.throttle is None:
            raise RuntimeError("failed to get a throttle for " + loc.name())
        self.debug("throttle is set, type is " + type(loc.throttle).__name__)

    # Determine what 'thing' is (string name of a block, the block itself, or the sensor of the block)
    # and return the layout block and the sensor (if there is one).
    def convertToLayoutBlockAndSensor(self, thing):
        if type(thing) == str:
            lb = layoutblocks.getLayoutBlock(thing)
            if lb is None:
                raise RuntimeError("no such block: " + thing)
            block = lb
            sensor = lb.getOccupancySensor()
        elif type(thing) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            # startBlock is a LayoutBlock
            block = thing
            sensor = thing.getOccupancySensor()
        elif type(thing) == jmri.Block:
            # thing is a Block
            lb = layoutblocks.getLayoutBlock(thing.getUserName())
            if lb is None:
                raise RuntimeError("no such layoutBlock: " + thing.getUserName())
            block = lb
            sensor = block.getOccupancySensor()
        else:
            # thing is the sensor
            sensor = thing
            block = layoutblocks.getBlockWithSensorAssigned(thing)
        return block, sensor

    # checks the JackStatus memory to see if an ESTOP status
    # has been set by the user, and exits immediately if so
    def checkStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        if int(mem.getValue()) == ESTOP:
            print "Alex: detected ESTOP status"
            return False
        return True


    # Gets a train from startBlock to endBlock and optionally slows it down
    # and stops it there. Tries to update block occupancy values.
    def shortJourney(self, direction, startBlock, endBlock,
                     normalSpeed, slowSpeed=None, slowTime=0, unlockOnBlock=False,
                     stopIRClear=None, routes=None, lock=None, passBlock=False, nextBlock=None):

        # check we're not in ESTOP status
        if self.checkStatus() is False:
            return False

        # Get a startBlock and endBlock converted to layoutBlocks and get their
        # sensors too.
        startBlock, startBlockSensor = self.convertToLayoutBlockAndSensor(startBlock)
        endBlock, endBlockSensor = self.convertToLayoutBlockAndSensor(endBlock)

        self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName())

        # if unlockOnBlock is set it means we remove the supplied lock when the block
        # with a matching name moves from ACTIVE to any other state. Get the sensor
        # we need to watch
        if unlockOnBlock and lock:
            unlockSensor = layoutblocks.getLayoutBlock(lock.replace(" Lock", "")).getBlock().getSensor()
        else:
            unlockSensor = None

        # set the throttle
        throttle = self.loco.throttle

        # self.debug("throttle is type " + type(throttle).__name__)
        # if type(throttle) == str:
        #     self.debug("throttle is " + throttle)
        
        # are we moving
        if throttle.getSpeedSetting() > 0:
            self.debug("we are already moving")
            moving = True
        else:
            moving = False


        # check if we know where we are if the startblock is not occupied
        if startBlockSensor.knownState != ACTIVE:
            print self.loco.dccAddr, "start block", startBlock.getUserName(), "is not occupied"
            if self.knownLocation is None:
                errstr = str(self.loco.dccAddr) +  "start block " + startBlock.getUserName() + "is not occupied and no known location"
                raise RuntimeError(errstr)
            if self.knownLocation != startBlock:
                raise RuntimeError("start block is not occupied and known location does not match start block")

        # check we are ok to start moving (ie. the target block is free)
        ok_to_go = False
        tries = 0
        while not ok_to_go:
            if endBlockSensor.knownState == ACTIVE:
                self.debug("my destination block is occupied")
                if lock:
                    # let another loco have the lock
                    self.debug("relinquishing lock on " + lock)
                    if self.checkLock(lock, self.loco):
                        self.unlock(lock, self.loco)
                if moving:
                    # stop!
                    print self.loco.dccAddr, "stopping"
                    throttle.setSpeedSetting(0)
                if tries < 40:
                    # wait ...
                    print self.loco.dccAddr, "waiting..."
                    time.sleep(5)
                    tries += 1
                else:
                    # give up.
                    raise RuntimeError("timeout waiting for endblock to be free")
            else:
                # check if we need to get the lock back
                if lock:
                    if not self.checkLock(lock):
                        self.debug("we relinquished a lock on " + lock + ", getting it back")
                        self.getLock(lock)
                ok_to_go = True

        # if we are already moving set the new throttle setting
        # before we set routes or we might get to the next turnout
        # too soon, too fast
        if moving:
            self.debug("we are already moving, setting normal speed: " +  normalSpeed)
            self.loco.setSpeedSetting(normalSpeed)

        # If we have a lock specified, check we've got it
        if lock:
            if not self.checkLock(lock, self.loco):
                self.debug("lock is supplied but we don't have lock, getting it")
                lock = self.getLock(lock, self.loco)
                if lock is False:
                    raise RuntimeError("lock specified but not held and attempt to get lock failed")

        # Set initial route. It is assumed that only the first route
        # needs to be set before we start moving.
        if routes is not None and len(routes) > 0:
            self.debug("setting initial route")
            self.setRoute(routes[0])

        # If we are stationary, and the current direction is different
        # from the direction requested, set direction
        if not moving and throttle.getIsForward() != direction:
            if direction is True:
                dir = 'forward'
                self.loco.forward()
            else:
                self.loco.reverse()
                dir = 'reverse'
            self.debug("set direction to " +  dir)

        # set throttle position if we're not already moving (if we
        # are moving we set the throttle earlier)
        if not moving:
            print self.loco.dccAddr, "Setting normal Speed", normalSpeed
            self.loco.setSpeedSetting(normalSpeed)

        # Set remaining routes
        if routes is not None and len(routes) > 1:
            self.debug("setting subsequent routes")
            for r in routes:
                if r == routes[0]:
                    continue
                self.setRoute(r)

        # wait for a sensor to change
        self.debug("waiting for destination block " + endBlock.userName + " to become active")
        sensorList = [endBlockSensor]
        if unlockSensor:
            sensorList.append(unlockSensor)
        changedList = []
        arrived = False
        while not arrived:
            while len(changedList) == 0:
                self.changedSensors(sensorList) # record the current states
                self.waitChange(sensorList, 5000)
                if self.checkStatus() is False:
                    return False
                changedList = self.changedSensors(sensorList) # get a list of sensors whose state has changed
            # check if we should release the lock
            if unlockSensor and unlockSensor in changedList:
                self.unlock(lock)
            # check if we have reached the endBlock
            if endBlockSensor in changedList:
                arrived = True

        self.debug("destination block " +  endBlock.userName +  " is active, we have arrived")

        # set the value in the new occupied block
        self.loco.setBlock(endBlock)

        # if there was a lock specified it means the calling method
        # wants us to release it now (unless passBlock is set)
        if lock is not None and passBlock == False:
            self.unlock(lock)


        # slow the loco down in preparation for a stop (if slowSpeed is set)
        if slowSpeed is not None and slowSpeed > 0:
            # slow train to 'slowspeed'
            throttle.setSpeedSetting(slowSpeed)

        if stopIRClear:
            # check if we have a sensor or the name of a sensor
            if type(stopIRClear) == str:
                stopIRClear = sensors.getSensor(stopIRClear)
            # wait till the IR sensor is clear
            if stopIRClear.knownState != ACTIVE:
                print self.loco.dccAddr, "waiting for IR sensor to be active"
                self.waitSensorActive(stopIRClear)
                print self.loco.dccAddr, "IR sensor active..."
            print self.loco.dccAddr, "waiting for IR sensor to be inactive"
            self.waitSensorInactive(stopIRClear)
            print self.loco.dccAddr, "IR sensor inactive..."
        elif slowTime > 0:
            # there is no IR sensor to wait for, wait the specified time
            self.waitMsec(slowTime)

        if passBlock is False:
            # stop the train
            if stopIRClear is not None:
                spd = -1  # emergency stop
            else:
                spd = 0   # normal stop
            throttle.setSpeedSetting(spd)
            self.waitMsec(250)
            throttle.setSpeedSetting(spd)

        # we know where we are now
        self.knownLocation = endBlock

        if passBlock is True:
            # wait until the endblock is empty
            self.debug("waiting until block " + endBlock.getId() + " is unoccupied")
            self.waitSensorInactive(endBlockSensor)
            if lock is not None:
                self.unlock(lock)
            # set the loco's block to 'nextBlock' which is the block
            # has now moved into (and which has no sensor)
            if nextBlock:
                self.loco.setBlock(nextBlock)
                self.knownLocation = nextBlock

        return True
                
    def handle(self):
        pass

        

