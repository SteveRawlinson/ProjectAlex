import jmri
import time
import random
import os
from jmri_bindings import *
from myroutes import *
import util
import datetime

DEBUG = True

# statuses
NORMAL = 0
STOPPING = 1
ESTOP = 2

# The Alex class provides a series of utility methods which can be used
# to control a locomotive around a layout. It is intended to be used as
# a parent to a particular journey class

# noinspection PyInterpreter
class Alex(util.Util, jmri.jmrit.automat.AbstractAutomaton):

    # init() is called exactly once at the beginning to do
    # any necessary configuration.
    def init(self):
        self.sensorStates = None
        self.platformWaitTimeMsecs = 10000
        return

    def debug(self, message):
        if DEBUG:
            print str(datetime.datetime.now()) + ' ' + str(self.loco.dccAddr) + ': ' + message

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

    def setTroublesomeTurnouts(self, route):
        for i in range(0, route.getNumOutputTurnouts()):
            t = route.getOutputTurnout(i)
            if t.getSystemName() in TROUBLESOME_TURNOUTS:
                s = route.getOutputTurnoutState(i)
                if s == CLOSED:
                    state = 'CLOSED'
                else:
                    state = 'THROWN'
                self.debug("setting troublesome turnout " + t.getSystemName() + " to state " + state)
                t.setCommandedState(s)


    # sets (triggers) a route
    def setRoute(self, route, sleeptime=1):
        print self.loco.dccAddr, 'setting route', route
        r = routes.getRoute(route)
        if r is None:
            raise RuntimeError("no such route: " + route)
        self.setTroublesomeTurnouts(r)
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
        waitTimeMsecs = int(self.platformWaitTimeMsecs + (random.random() * (self.platformWaitTimeMsecs / 2)))
        self.waitMsec(waitTimeMsecs)

    # Gets a DCC throttle for the loco supplied
    def getLocoThrottle(self, loc):
        throttleAttempts = 0
        while throttleAttempts < 2 and loc.throttle is None:
            time.sleep(5)
            loc.throttle = self.getThrottle(loc.dccAddr, loc.longAddr())
            throttleAttempts += 1
        if loc.throttle is None:
            raise RuntimeError("failed to get a throttle for " + loc.name())
        self.debug("throttle is set, type is " + type(loc.throttle).__name__)


    # Returns the value of the JACKSTATUS memory
    def getJackStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        return mem.getValue()

    # The loco should be moving towards the loop already. This
    # method puts the loco into the loop and either stops it (if
    # stop is True) or gets it out again
    def reverseLoop(self, loop, stop = True):
        inroute, outroute = ROUTEMAP[loop]
        self.setRoute(inroute)
        oSensor = layoutblocks.getLayoutBlock(loop).getOccupancySensor()
        irSensor = sensors.getSensor(IRSENSORS[loop])
        if oSensor.knownState != ACTIVE:
            self.debug("reverseLoop: waiting for occupancy sensor to go active")
            self.waitChange([oSensor])
            self.loco.setBlock(loop)
        if irSensor.knownState != ACTIVE:
            self.debug('reverseLoop: waiting for IR sensor to go active')
            self.waitChange([irSensor])
        self.debug('reverseLoop: waiting for IR sensor to go inactive')
        self.waitChange([irSensor])
        if stop:
            self.debug('reverseLoop: stopping loco and returning')
            self.loco.setSpeedSetting(-1)
            return
        self.debug('reverseLoop: setting exit route and returning')
        self.setRoute(outroute)
        self.loco.unselectReverseLoop(loop)
        return

    # Checks two places to get the slowtime - the number of seconds to
    # move at slowSpeed before coming to a halt at a platform. It first
    # calls the loco.getSlowTimes() method which returns a hash defined in
    # myroutes.py. If that does't work it tries
    #  to find a method called getSlowTimes() defined in the journey
    # class (ie. the class that is the child of this class) which returns a hash
    # (or whatever they're called in python).
    def getSlowtime(self, destination):
        st = self.loco.slowTimes()
        if st is not None:
            if destination in st:
                return st[destination]
        try:
            callable(self.getSlowTimes)
        except AttributeError, e:
            self.debug("**************************** can't find slowtime for " + self.loco.nameAndAddress() + " at " + destination + "******************************")
            return 1
        st = self.getSlowTimes()
        if st[destination] is not None:
            return st[destination]
        self.debug("**************************** can't find slowtime for " + self.loco.nameAndAddress() + " at " + destination + "******************************")
        return 1

    # Gets a train from startBlock to endBlock and optionally slows it down
    # and stops it there. Tries to update block occupancy values.
    #
    # params:
    # direction: True for forwards, False for reverse
    # startBlock: the block the loco is in (can be a name, a Block or s LayoutBlock)
    # endBlock: the destination block
    # normalSpeed: the speed (0 = stop, 1 = full speed) to spend most of the journey
    # slowSpeed: the speed to reduce to once we enter the endBlock
    # slowTime: the time (in msec) to spend at SlowSpeed before stopping (values under 200 are assumed to be seconds)
    # unlockOnBlock: (boolean) unlock the supplied lock when the block that is locked goes inactive if True
    # stopIRClear: (Sensor or String) the sensor (or name of the sensor) which will go inactive when it's safe to stop
    # routes: list of Route objects to set (ie. activate)
    # lock: (String) name of a lock we need to unlock when we're done
    # passBlock: (boolean) wait until the endBlock is empty before returning (and don't stop the loco)
    # nextBlock: the block after endBlock (which is not monitored by an occupancy sensor)
    # dontSrop: (boolean) if true, don't stop the loco
    def shortJourney(self, direction, startBlock, endBlock,
                     normalSpeed, slowSpeed=None, slowTime=None, unlockOnBlock=False,
                     stopIRClear=None, routes=None, lock=None, passBlock=False, nextBlock=None, dontStop=None):

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            return RuntimeError("shortJourney called while status is ESTOP")

        # passBlock implies dontStop
        if dontStop is None:
            if passBlock is True:
                dontStop = True
            else:
                dontStop = False
        if dontStop is False and passBlock is True:
            raise RuntimeError("dontStop can't be false if passBlock is true")

        # convert string speeds to floats
        origNormalSpeed = 'dunno'
        if type(normalSpeed) == str or type(normalSpeed) == unicode:
            origNormalSpeed = normalSpeed
            normalSpeed = self.loco.speed(normalSpeed)
        if type(slowSpeed) == str or type(slowSpeed) == unicode:
            slowSpeed = self.loco.speed(slowSpeed)

        # Get a startBlock and endBlock converted to layoutBlocks and get their
        # sensors too.
        startBlock, startBlockSensor = self.convertToLayoutBlockAndSensor(startBlock)
        endBlock, endBlockSensor = self.convertToLayoutBlockAndSensor(endBlock)

        self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName())

        # slowSpeed implies slowTime (if there's no IR sensor involved)
        if slowSpeed is not None and stopIRClear is None:
            if slowTime is None:
                slowTime = self.getSlowtime(endBlock.getUserName())
        # convert slowTime to msecs
        if 0 < slowTime < 200:
            slowTime = int(slowTime * 1000)


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
            startTime = time.time()
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
                    self.loco.setSpeedSetting(0)
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
        if moving and normalSpeed is not None:
            self.debug("we are already moving, setting normal speed: " +  str(normalSpeed))
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
            if normalSpeed is None:
                raise RuntimeError("normalSpeed is None (was specified as " + str(origNormalSpeed) + ")")
            startTime = time.time()
            print self.loco.dccAddr, "not moving, setting normal Speed", normalSpeed
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
        slowJourneyStart = time.time()
        while not arrived:
            while len(changedList) == 0:
                self.changedSensors(sensorList) # record the current states
                self.waitChange(sensorList, 5000)
                if self.getJackStatus() == ESTOP:
                    return False
                if time.time() - slowJourneyStart > 30 * 60.0: # 30 minute timeout
                    raise RuntimeError("shortJourney took too long")
                changedList = self.changedSensors(sensorList) # get a list of sensors whose state has changed
            # check if we should release the lock
            if unlockSensor and unlockSensor in changedList:
                self.unlock(lock)
            # check if we have reached the endBlock
            if endBlockSensor in changedList:
                arrived = True

        arriveTime = time.time()
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
            if self.isBlockVisible(endBlock) and stopIRClear is None:
                self.debug("gradually setting slowSpeed: " + str(slowSpeed))
                self.loco.graduallyChangeSpeed(slowSpeed)
            else:
                self.debug("setting slowSpeed" + str(slowSpeed))
                self.loco.setSpeedSetting(slowSpeed)

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
        elif slowTime and slowTime > 0:
            # there is no IR sensor to wait for, wait the specified time
            self.debug(" ********************** waiting slowtime at " + endBlock.getId() + ' :' + str(slowTime / 1000) + " **********************************************")
            self.waitMsec(slowTime)

        if dontStop is False:
            # stop the train
            if stopIRClear is not None:
                spd = -1  # emergency stop
            else:
                spd = 0   # normal stop
                self.debug("being loco to a halt")
            self.loco.setSpeedSetting(spd)
        else:
            self.debug("not stopping loco")

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

        finishTime = time.time()
        logStr = self.loco.nameAndAddress() + ',' + startBlock.getUserName() + ',' + endBlock.getUserName() + ',' + str(startTime) + \
                 ',' + str(arriveTime) + ',' + str(finishTime) + ',' + str(arriveTime - startTime) + "\n"
        logfile = open('startJourney.log', 'a')
        logfile.write(logStr)
        logfile.close()

        return True
                

    # moves a train from their current block into the north sidings
    def moveIntoNorthSidings(self, lock=None):
        trak = track.Track.findTrackByBlock(self.loco.block)
        routes = [trak.exitRoute(trak.southbound())]
        if lock is None:
            self.getLock('North Link Lock')
        b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        if not self.loco.reversible() and b is not None:
            # we need a reverse loop and it's available
            for r in routes:
                self.setRoute(r)
            speed = self.loco.speed('into reverse loop', 'fast')
            self.loco.setSpeedSetting(speed)
            self.reverseLoop(NORTH_REVERSE_LOOP)
        elif self.getJackStatus() == NORMAL and self.loco.rarity() == 0 and self.loco.reversible():
            # If this loco has a rarity of zero and we're not shutting down operations
            # there's no point in going all the way to the sidings because we'll just get
            # started up again. Stop on the North Link
            self.debug("stopping early")
            speed = self.loco.speed('track to north link', 'medium')
            self.shortJourney(False, self.loco.block, "North Link", speed, slowSpeed=speed, routes=routes)
            # check JackStatus hasn't changed in the meantime
            if self.getJackStatus() == STOPPING:
                self.debug("JackStatus is now STOPPING - moving to siding")
                siding = self.loco.selectSiding(NORTH_SIDINGS)
                routes = self.requiredRoutes(siding)
                self.shortJourney(False, self.loco.block, siding, 'fast', stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        else:
            # self.debug("not stopping early. status :" + str(self.getJackStatus()) + " doesn't equal normal: " + str(NORMAL) + " self.rarity(): " + str(self.loco.rarity()))
            siding = self.loco.selectSiding(NORTH_SIDINGS)
            speed = self.loco.speed('track to north link', 'medium')
            if self.loco.reversible():
                dir = False
            else:
                dir = True
            self.shortJourney(dir, self.loco.block, "North Link", speed, routes=routes, lock=lock)
            routes = self.requiredRoutes(siding)
            speed = self.loco.speed('north link to sidings', 'fast')
            self.shortJourney(dir, self.loco.block, siding, speed, stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
        if b:
            self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)


    def handle(self):
        pass

        

