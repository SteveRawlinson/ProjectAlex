import sys
import jmri
import time
import random
import os
from jmri_bindings import *
from myroutes import *
import util
import datetime
import track
import lock
import pprint
import loco
from javax.swing import JOptionPane

DEBUG = True

# statuses
NORMAL = 0
STOPPING = 1
ESTOP = 2

class EstopError(RuntimeError):
    pass

# The Alex class provides a series of utility methods which can be used
# to control a locomotive around a layout. It is intended to be used as
# a parent to a particular journey class

# noinspection PyInterpreter
class Alex(util.Util, jmri.jmrit.automat.AbstractAutomaton):

    def __init__(self, loc, memory, track):
        self.loco = loc
        self.knownLocation = None
        self.memory = memory
        self.track = track
        self.allRoutesSet = False
        self.lastRouteSetTime = None
        #self.tracks = []
        #self.initTracks()

    # init() is called exactly once at the beginning to do
    # any necessary configuration.
    def init(self):
        self.sensorStates = None
        self.platformWaitTimeMsecs = 20000
        return

    def debug(self, message):
        if DEBUG:
            calling_method = sys._getframe(1).f_code.co_name
            if hasattr(self, 'loco') and self.loco is not None:
                addr = str(self.loco.dccAddr)
            else:
                addr = 'unknown'
            s = str(datetime.datetime.now()) + ' ' + addr + ': ' + calling_method + ': ' + message
            print s
            self.log(message)

    # # Get's a 'lock' on a memory variable. It sets the variable
    # # to the loco number but only if the value is blank. If
    # # it's already got a value then we wait for a while to see
    # # if it clears, otherwise we give up.
    # def getLock(self, mem, loco=None):
    #     if loco is None:
    #         loco = self.loco
    #     lock = False
    #     tries = 0
    #     while lock is not True:
    #         print loco.dccAddr, "getting lock on", mem
    #         value = memories.getMemory(mem).getValue()
    #         if value == str(loco.dccAddr):
    #             self.debug("already had a lock, returning")
    #             return mem
    #         if value is None or value == '':
    #             memories.getMemory(mem).setValue(str(loco.dccAddr))
    #             time.sleep(1)
    #             value = memories.getMemory(mem).getValue()
    #             if value == str(loco.dccAddr):
    #                 self.debug("lock acquired")
    #                 lock = True
    #             else:
    #                 # race condition and we lost
    #                 tries += 1
    #                 if tries < 20:
    #                     print loco.dccAddr, "new memory setting did not stick, trying again"
    #                     time.sleep(5)
    #                 else:
    #                     print loco.dccAddr, "giving op on lock"
    #                     raise RuntimeError(str(loco.dccAddr) + ": giving up getting lock on " + mem)
    #         else:
    #             # link track is busy
    #             tries += 1
    #             if tries < 40:
    #                 print loco.dccAddr, "track is locked, waiting ..."
    #                 time.sleep(5)
    #             else:
    #                 print loco.dccAddr, "giving up on lock"
    #                 raise RuntimeError(str(loco.dccAddr) + ": giving up getting lock on " + mem)
    #     return mem
    #
    # # Attempts to get a lock and returns immediately whether or
    # # not the attempt was successful. No race condition testing
    # # is done, the calling function can do that with checkLock()
    # def getLockNonBlocking(self, mem, loco = None):
    #     if loco is None:
    #         loco = self.loco
    #     self.debug("getting non-blocking lock on " + str(mem))
    #     value = memories.getMemory(mem).getValue()
    #     if value == str(loco.dccAddr):
    #         return mem
    #     if value is None or value == '':
    #         memories.getMemory(mem).setValue(str(loco.dccAddr))
    #         return mem
    #     self.debug("failed to get non-blocking lock on" +  mem)
    #     return False

    def getLock(self, mem):
        if "North" in mem:
            end = NORTH
            end_s = "North"
        else:
            end = SOUTH
            end_s = "South"
        if self.loco.dir() == "Nth2Sth":
            dir = SOUTHBOUND
        else:
            dir = NORTHBOUND
        self.debug("getting (old) lock on " + end_s + " Link")
        lck = lock.Lock()
        lck.getOldLock(end, dir, self.loco)
        self.debug(lck.status())
        return lck

    def getLockNonBlocking(self, mem):
        if "North" in mem:
            end = NORTH
            end_s = "North"
        else:
            end = SOUTH
            end_s = "South"
        if self.loco.dir() == "Nth2Sth":
            dir = SOUTHBOUND
        else:
            dir = NORTHBOUND
        self.debug("getting non blocking lock on " + end_s + " Link")
        lck = lock.Lock()
        lck.getOldLockNonBlocking(end, dir, self.loco)
        if lck.empty():
            self.debug("failed to get lock")
            return False
        self.debug(lck.status())
        return lck

    def unlock(self, lck):
        if DEBUG:
            if not lck.empty():
                if lck.end == NORTH:
                    end_s = 'North'
                else:
                    end_s = 'South'
                self.debug("unlocking " + end_s + " Link")
            lck.unlock()

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
        #print loco.dccAddr, "does not have lock on ", mem
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
    def setRoute(self, route, sleeptime=None, waitTillNotBusy=False):
        self.debug('setting route ' +  str(route))
        r = routes.getRoute(route)
        if r is None:
            raise RuntimeError("no such route: " + route)
        #self.setTroublesomeTurnouts(r)
        #r.activateRoute()
        r.setRoute()
        self.lastRouteSetTime = time.time()
        if sleeptime is not None and sleeptime > 0:
            time.sleep(sleeptime)
        if waitTillNotBusy and r.isRouteBusy():
            self.debug("waiting till route is not busy")
            while r.isRouteBusy():
                time.sleep(0.2)
            self.debug("route not busy")

    # Iterates through a list of sidings and makes sure we know
    # the identity of the loco in those which are occupied
    def whatsInSidings(self, sidings):
        for s in sidings:
            self.debug("checking siding " + s)
            if self.isBlockOccupied(s):
                addr = self.getBlockContents(s)
                if addr is None or addr == '':
                    self.debug("  getting loco from user")
                    addr = JOptionPane.showInputDialog("DCC loco in: " + s)
                    if addr is None or addr == "":
                        continue
                    addr = int(addr)
                loc = loco.Loco.getLocoByAddr(addr, self.locos)
                if loc is None:
                    self.debug("  new loco addr " + str(addr) + " found")
                    loc = loco.Loco(int(addr))
                self.locos.append(loc)
                self.debug("setting + " + loc.nameAndAddress() + " block to " + s)
                loc.setBlock(s)
            else:
                self.debug("  not occupied")

    def clearSidings(self, end):
        list = []
        if end == NORTH:
            sidings = NORTH_SIDINGS
        else:
            sidings = SOUTH_SIDINGS
        # check we know what's there
        self.whatsInSidings(sidings)
        # get the tracks
        self.initTracks()
        usedblocks = []
        for s in sidings:
            self.debug("checking siding " + s)
            if not self.isBlockOccupied(s):
                self.debug("  not occupied")
                continue
            block = blocks.getBlock(s)
            self.debug("  block value: " + str(block.getValue()) )
            loc = loco.Loco.getLocoByAddr(block.getValue(), self.locos)
            self.debug("  loco: " + loc.nameAndAddress())
            # work out where we're going to put this loco
            chosenblock = None
            prevBlock = None
            for t in self.tracks[::-1]:
                self.debug("    checking " + t.name())
                if end == SOUTH:
                    blocklist = t.blocks[:] # copy
                else:
                    blocklist = t.blocks[::-1] # reversed copy
                for b in blocklist:
                    self.debug("      checking block " + b)
                    i = blocklist.index(b)
                    if self.isBlockOccupied(b) or b in usedblocks:
                        self.debug(    "      block is occupied or already chosen")
                        if i == 0:
                            # first block, can't use this track
                            self.debug("      can't use this track, next ")
                            break
                        else:
                            chosenblock = blocklist[i - 1]
                            if i > 1:
                                prevBlock = blocklist[i - 2]
                            break
                    else:
                        if i == len(blocklist) - 1:
                            # last block
                            chosenblock = b
                            if i > 1:
                                prevBlock = blocklist[i - 2]
                            break
                if chosenblock:
                    self.debug("        choosing block " + chosenblock)
                    list.append([loc, t, chosenblock, s, prevBlock])
                    usedblocks.append(chosenblock)
                    break
            if chosenblock is None:
                self.debug("unable to find enough free blocks")
                return False
        locolist = []
        for i in list:
            loc = i[0]
            trak = i[1]
            blok = i[2]
            siding = i[3]
            prevBlock = i[4]
            self.debug("moving loco " + loc.nameAndAddress() + " from " + siding + " to " + trak.name() + " block " + blok)
            routes = self.requiredRoutes(siding)
            if trak.southbound() and end == NORTH or trak.northbound() and end == SOUTH:
                rightway = True
            else:
                rightway = False
            routes.append(trak.exitRoute(rightway))
            self.loco = loc
            self.getLocoThrottle(loc)
            self.shortJourney(end == NORTH, siding, blok, 'medium', slowTime=1, slowSpeed='slow', routes=routes, clearThisBlock=prevBlock)
            locolist.append(str(loc.dccAddr))
        if end == NORTH:
            memname = 'IMNORTHSIDINGSEMPTIED'
        else:
            memname = 'IMSOUTHSIDINGSEMPTIED'
        mem = memories.provideMemory(memname)
        mem.setValue(','.join(locolist))
        return True




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

    def waitAtPlatform(self):
        if self.getJackStatus() == STOPPING:
            wt = self.platformWaitTimeMsecs / 2
        else:
            wt = self.platformWaitTimeMsecs
        self.debug("waiting at platform for " + str(self.platformWaitTimeMsecs / 1000) + " secs")
        self.waitMsec(wt)

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
        return int(mem.getValue())

    # The loco should be moving towards the loop already. This
    # method puts the loco into the loop and either stops it (if
    # stop is True) or gets it out again
    def reverseLoop(self, loop, stop = True, lock=None):
        inroute, outroute = ROUTEMAP[loop]
        self.setRoute(inroute)
        oSensor = layoutblocks.getLayoutBlock(loop).getOccupancySensor()
        irSensor = sensors.getSensor(IRSENSORS[loop])
        if oSensor.knownState != ACTIVE:
            self.debug("reverseLoop: waiting for occupancy sensor to go active")
            self.waitChange([oSensor])
            self.loco.setBlock(loop)
            if lock and lock.full():
                lock.unlock(partialUnlock=True)
        sp = self.loco.speed('in reverse loop', 'medium')
        self.loco.setSpeedSetting(sp)
        if irSensor.knownState != ACTIVE:
            self.debug('reverseLoop: waiting for IR sensor to go active')
            self.waitChange([irSensor])
        self.debug('reverseLoop: waiting for IR sensor to go inactive')
        self.waitChange([irSensor])
        if lock:
            lock.unlock()
            lock.logLock()
        if stop:
            self.debug('reverseLoop: stopping loco and returning')
            self.loco.setSpeedSetting(0)
            return
        self.debug('reverseLoop: setting exit route and returning')
        self.setRoute(outroute)
        self.loco.unselectReverseLoop(loop)
        return

    # Gets the slowtime - the number of seconds to
    # move at slowSpeed before coming to a halt at a platform.
    # Slowtimes are defined in myroutes. If there is no
    # slowtime defined for the loco at the destination
    # it returns a default of 1.
    def getSlowtime(self, destination):
        return self.loco.getSlowtime(destination)

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
    # lock: (String or Lock) name of a lock we need to unlock when we're done
    # passBlock: (boolean) wait until the endBlock is empty before returning (and don't stop the loco)
    # nextBlock: the block after endBlock (which is not monitored by an occupancy sensor)
    # dontStop: (boolean) if true, don't stop the loco
    # endIRSensor: use this sensor to indicate arrival rather than endBlock's sensor
    # lockSensor: wait until this sensor (or the sensor this string indicates) is inactive before releasing supplied lock
    # eStop: issue an emergency stop rather than an idle command when stopping the loco
    # ignoreOccupiedEndblock: long trains are sometimes in their destination block already
    # lockToUpgrade: a lock which needs upgrading from a partial asap in order to give routes time. We try to upgrade it while we're waiting for sensors
    # upgradeLockRoutes: routes to be set after the lock is upgraded
    # clearThisBlock: make sure this block is not occupied before we stop the loco
    def shortJourney(self, direction, startBlock=None, endBlock=None, normalSpeed=None, slowSpeed=None, slowTime=None, unlockOnBlock=False,
                     stopIRClear=None, routes=None, lock=None, passBlock=False, nextBlock=None, dontStop=None, endIRSensor=None,
                     lockSensor=None, eStop=False, ignoreOccupiedEndBlock=False, lockToUpgrade=None, upgradeLockRoutes=None, clearThisBlock=None):

        self.log("startJourney called")

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # wait until the power comes back on
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)

        # passBlock implies dontStop
        if dontStop is None:
            if passBlock is True:
                dontStop = True
            else:
                dontStop = False
        if dontStop is False and passBlock is True:
            raise RuntimeError("dontStop can't be false if passBlock is true")

        # Default speed
        if normalSpeed is None:
            normalSpeed = self.loco.speed('medium')

        # Default start block
        if startBlock is None:
            startBlock = self.loco.block

        # must have endBlock
        if endBlock is None:
            raise RuntimeError("must specify endBlock")

        # convert lockSensor
        if lockSensor and type(lockSensor) != jmri.Sensor:
            lockSensor = sensors.getSensor(lockSensor)

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
        if clearThisBlock:
            clearBlock, clearBlockSensor = self.convertToLayoutBlockAndSensor(clearThisBlock)

        if routes:
            self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName() + " routes: " + ', '.join(routes))
        else:
            self.debug('shortjourney: ' + startBlock.getUserName() + " -> " + endBlock.getUserName() + " routes: None")

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
            unlockSensor = layoutblocks.getLayoutBlock(lock.replace(" lock", "")).getBlock().getSensor()
        else:
            unlockSensor = None

        # set the throttle
        throttle = self.loco.throttle
        if self.loco.throttle.getLocoNetSlot() is None:
            self.debug("loco throttle has no slot, getting a new throttle")
            self.getLocoThrottle(self.loco)

        # turn lights on
        self.loco.throttle.setF0(True)

        # are we moving
        if self.loco.throttle.getSpeedSetting() > 0:
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
        arrived = False
        tries = 0
        while not ok_to_go:
            if endBlockSensor.knownState == ACTIVE:
                if lock and not lock.empty() and 'ink' in endBlock.getId():
                    # The block is a link and we have a lock so
                    # we can safely ignore the occupied block
                    self.debug("ignoring occupied endblock: it's a link and we have a lock")
                    ok_to_go = True
                if ignoreOccupiedEndBlock:
                    # calling method specifically says don't bother with this check
                    self.debug("ignoring occupied endBlock: flag set")
                    ok_to_go = True
                    arrived = True
                else:
                    self.debug("my destination block " + endBlock.getId() + " is occupied")
                    if lock:
                        # let another loco have the lock
                        if type(lock) != str and type(lock) != unicode:
                            if not lock.empty():
                                self.debug("relinquishing lock")
                                lock.unlock()
                        else:
                            self.debug("relinquishing lock")
                            self.unlock(lock)
                    if moving:
                        # stop!
                        self.debug("stopping loco")
                        self.loco.setSpeedSetting(0)
                    if tries < 300:
                        # wait ...
                        time.sleep(1)
                        tries += 1
                    else:
                        # give up.
                        raise RuntimeError("timeout waiting for endblock to be free")
            else:
                ok_to_go = True

        # if we are already moving set the new throttle setting
        # before we set routes or we might get to the next turnout
        # too soon, too fast
        if moving and normalSpeed is not None:
            self.debug("we are already moving, setting normal speed: " +  str(normalSpeed))
            if self.isBlockVisible(self.loco.block):
                self.loco.graduallyChangeSpeed(normalSpeed)
            else:
                self.loco.setSpeedSetting(normalSpeed)

        # If we have a lock specified, check we've got it
        if lock:
            if type(lock) != str and type(lock != unicode):
                if lock.empty():
                    lock.getLock(lock.end, lock.direction, lock.loco)
            else:
                if not self.checkLock(lock, self.loco):
                    self.debug("lock is supplied but we don't have lock, getting it")
                    lock = self.getLock(lock)


        # Set initial route. It is assumed that only the first route
        # needs to be set before we start moving unless we're in a siding because
        # then the route order can be naughty
        subsequentRoutesSet = False
        if routes is not None and len(routes) > 0:
            self.debug("setting initial route")
            self.setRoute(routes[0])
            if "iding" in startBlock.getId() and not moving:
                self.debug("in sidings and not moving; setting subsequent routes")
                for r in routes:
                    if r == routes[0]:
                        continue
                    self.setRoute(r)
                subsequentRoutesSet = True
                # sidings have a lot of points to move
                time.sleep(4)

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
            self.debug("not moving, setting normal Speed: " +  str(normalSpeed))
            self.loco.setSpeedSetting(normalSpeed)

        # Set remaining routes if there are any
        if routes is not None and len(routes) > 1 and not subsequentRoutesSet:
            self.debug("setting subsequent routes")
            for r in routes:
                if r == routes[0]:
                    continue
                self.setRoute(r)

        #
        #  ----------------  wait for a sensor to change  (unless we've arrived) ------------------------------------------
        #
        self.debug("waiting for destination block " + endBlock.userName + " to become active")
        if endIRSensor is not None:
            sensorList = [endIRSensor]
        else:
            sensorList = [endBlockSensor]
        if unlockSensor:
            sensorList.append(unlockSensor)
        changedList = []
        shortJourneyStart = time.time()
        while not arrived:
            repeatedSpeed = False
            while len(changedList) == 0:
                self.changedSensors(sensorList) # record the current states
                # wait for sensors to change
                self.waitChange(sensorList, 500)
                if self.getJackStatus() == ESTOP:
                    # abort
                    self.debug("aborting shortJourney, ESTOP status detected")
                    self.loco.emergencyStop()
                    raise EstopError("Estop")
                # else:
                    # self.debug("getJackStatus(): " + str(self.getJackStatus()) + " " + type(self.getJackStatus()).__name__ + "ESTOP: " + str(ESTOP) + ' ' + type(ESTOP).__name__  + " don't match")
                if repeatedSpeed is False and time.time() - shortJourneyStart > 3.0:
                    # send a gentle reminder of the speed after 3 seconds
                    self.loco.repeatSpeedMessage(normalSpeed)
                    repeatedSpeed = True
                if time.time() - shortJourneyStart > 30 * 60.0:
                    # 30 minute timeout
                    raise RuntimeError("shortJourney took too long")
                # if lockToUpgrade is set, we have a partial lock which we'd like to
                # upgrade sooner rather than later to give any additional routes time
                # to fire without having to slow the loco down
                if lockToUpgrade and lockToUpgrade.partial():
                    if lockToUpgrade.upgradeLockNonBlocking(keepOldPartial=True):
                        lockToUpgrade.writeMemories()
                        self.debug("lock upgrade successful")
                        if upgradeLockRoutes is not None:
                            self.debug("setting additional routes")
                            for r in upgradeLockRoutes:
                                self.setRoute(r)
                            self.allRoutesSet = True
                # get a list of sensors whose state has changed (might be empty)
                changedList = self.changedSensors(sensorList)
            # a sensor has changed
            # check if we should release the lock
            if unlockSensor and unlockSensor in changedList:
                lock.unlock()
                lock.logLock()
            # check if we have reached the endBlock
            if endBlockSensor in changedList or endIRSensor in changedList:
                arrived = True

        # we have arrived
        arriveTime = time.time()
        if endIRSensor:
            self.debug("destination block IR sensor at " + endBlock.userName + " is active, we have arrived")
        else:
            self.debug("destination block " + endBlock.userName + " is active, we have arrived")

        # set the value in the new occupied block
        self.loco.setBlock(endBlock)

        # if there was a lock specified it means the calling method
        # wants us to release it now, unless passBlock is set (which means
        # wait until we are past the endBlock before releasing lock) or
        # lockSensor is set (which means wait until that sensor is inactive,
        # which we do later)
        if lock is not None and passBlock == False:
            if lockSensor and lockSensor.getKnownState() == ACTIVE:
                pass
            else:
                lock.unlock()
                lock.logLock()
                lock = None

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # slow the loco down in preparation for a stop (if slowSpeed is set)
        if slowSpeed is not None and slowSpeed > 0:
            # slow train to 'slowspeed'
            if self.isBlockVisible(endBlock) and stopIRClear is None:
                self.debug("gradually setting slowSpeed: " + str(slowSpeed))
                self.loco.graduallyChangeSpeed(slowSpeed)
            else:
                self.debug("setting slowSpeed: " + str(slowSpeed))
                self.loco.setSpeedSetting(slowSpeed)

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # if we didn't unlock above because the lockSensor was still active,
        # do it now.
        if lock and lockSensor:
            if lockSensor.getKnownState() == ACTIVE:
                # still active, wait
                self.log("waiting for lockSensor to go inactive before releasing lock")
                self.waitChange([lockSensor])
            lock.unlock()
            lock.logLock()

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        if stopIRClear:
            # check if we have a sensor or the name of a sensor
            if type(stopIRClear) == str:
                stopIRClear = sensors.getSensor(stopIRClear)
            # wait till the IR sensor is clear
            if stopIRClear.knownState != ACTIVE:
                self.debug("waiting for IR sensor " + stopIRClear.getDisplayName() + " to be active")
                self.waitSensorActive(stopIRClear)
                self.debug("IR sensor active")
            self.debug("waiting for IR sensor " + stopIRClear.getDisplayName() + " to be inactive")
            self.waitSensorInactive(stopIRClear)
            self.debug("IR sensor " + stopIRClear.getDisplayName() + " inactive...")
        elif slowTime and slowTime > 0:
            # there is no IR sensor to wait for, wait the specified time
            self.debug(" ********************** waiting slowtime at " + endBlock.getId() + ' :' + str(slowTime / 1000) + " **********************************************")
            self.waitMsec(slowTime)

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # wait till we've cleared this block
        if clearThisBlock:
            if clearBlockSensor.knownState == ACTIVE:
                self.debug("waiting till block " + clearBlock.getId() + " is clear before stopping loco")
                self.waitSensorInactive(clearBlockSensor)

        if dontStop is False:
            # stop the train
            if stopIRClear is not None or eStop is True:
                self.loco.emergencyStop()
            else:
                self.loco.setSpeedSetting(0)
                self.debug("bringing loco to a halt in block " + endBlock.userName)

        else:
            self.debug("not stopping loco")

        # we know where we are now
        self.knownLocation = endBlock

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        if passBlock is True:
            # wait until the endblock is empty
            self.debug("waiting until block " + endBlock.getId() + " is unoccupied")
            self.waitSensorInactive(endBlockSensor)
            if lock is not None:
                lock.unlock()
                lock.logLock()
            # set the loco's block to 'nextBlock' which is the block
            # has now moved into (and which has no sensor)
            if nextBlock:
                self.loco.setBlock(nextBlock)
                self.knownLocation = nextBlock

        finishTime = time.time()
        logStr = self.loco.nameAndAddress() + ',' + startBlock.getUserName() + ',' + endBlock.getUserName() + ',' + str(startTime) + \
                 ',' + str(arriveTime) + ',' + str(finishTime) + ',' + str(arriveTime - startTime) + "\n"
        logfile = open('C:\Users\steve\shortJourney.log', 'a')
        logfile.write(logStr)
        logfile.close()

        return True
                

    # moves a train from their current block into the north sidings
    def moveIntoNorthSidings(self, lock=None, speed=None):

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # wait until the power comes back on
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)

        # deal with locking
        if type(lock) == str or type(lock) == unicode:
            raise RuntimeError("old style lock used with moveIntoSouthSidings")
        if lock is None or lock.empty():
            if self.loco.throttle.getSpeedSetting() > 0:
                # we need a lock promptly or we must stop
                lock = self.loco.getLockNonBlocking(NORTH)
            else:
                # we are stationary, we can wait for a lock
                if self.loco.rarity() == 0.0:
                    sleepTime = 5 # no hurry for the lock
                else:
                    sleepTime = None # get getLock() decide
                lock = self.loco.getLock(NORTH, sleepTime=sleepTime)
        if lock.empty():
            self.track.setExitSignalAppearance(RED)
            # bring loco to a halt
            self.loco.graduallyChangeSpeed('slow')
            time.sleep(self.getSlowtime(self.loco.block.getUserName()))
            self.loco.setSpeedSetting(0)
            lock.getLock(NORTH, NORTHBOUND, self.loco)
            self.debug(lock.status())
        self.track.setExitSignalAppearance(GREEN)

        # remove the memory
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)
        mem = memories.provideMemory("IMTRACK" + str(self.track.nr) + "LOCO")
        mem.setValue(None)
        mem = memories.provideMemory("IMTRACK" + str(self.track.nr) + "SPEED")
        mem.setValue(None)
        self.debug("set memory IMTRACK" + str(self.track.nr) + "SPEED to None: new value: " + str(mem.getValue()))

        route = self.track.exitRoute(self.track.southbound())
        routes = [route]
        if lock is None:
            lock = self.loco.getLock(NORTH)
        elif hasattr(lock, 'empty') and lock.empty():
            lock.getLock(NORTH)
        if not self.loco.reversible():
            b = self.loco.selectReverseLoop(NORTH_REVERSE_LOOP)
        if not self.loco.reversible() and b is not None:
            # we need a reverse loop and it's available
            self.debug("moving into North reverse loop")
            if speed is None:
                speed = self.loco.speed('off track north', 'medium')
            self.shortJourney(True, self.loco.block, self.loco.track.nextBlockNorth(self.loco.block), speed, dontStop=True, routes=[route])
            speed = self.loco.speed('north interlink northbound', 'medium')
            self.shortJourney(True, self.loco.block, 'North Link', speed, dontStop=True, routes=[route])
            # reverse loops are used by long trains, be more cautious with locks
            if lock.partial():
                self.loco.setSpeedSetting(0)
                lock.upgradeLock(keepOldPartial=True)
            self.track.setExitSignalAppearance(GREEN)
            speed = self.loco.speed('into reverse loop', 'fast')
            self.loco.setSpeedSetting(speed)
            self.reverseLoop(NORTH_REVERSE_LOOP, lock=lock)
            self.loco.unselectReverseLoop(NORTH_REVERSE_LOOP)
        elif self.getJackStatus() == NORMAL and self.loco.rarity() == 0 and self.loco.reversible():
            # If this loco has a rarity of zero and we're not shutting down operations, and it hasn't been retired
            # there's no point in going all the way to the sidings because we'll just get
            # started up again. Stop on the North Link.
            self.debug("stopping early")
            if speed is None:
                speed = self.loco.speed('off track north', 'medium')
            self.shortJourney(False, self.loco.block, self.loco.track.nextBlockNorth(self.loco.block), speed, dontStop=True, routes=[route])
            speed = self.loco.speed('north interlink northbound', 'medium')
            self.shortJourney(False, self.loco.block, 'North Link', normalSpeed=speed, slowSpeed=speed, routes=[route], eStop=True)
            if lock.partial():
                # we should get the full lock straight away
                lock.upgradeLock(keepOldPartial=True)
            # check JackStatus hasn't changed in the meantime
            if self.getJackStatus() == STOPPING:
                self.debug("JackStatus is now STOPPING - moving to siding")
                siding = self.loco.selectSiding(NORTH_SIDINGS, blocking=False)
                if siding is None:
                    self.debug("no sidings available, JackStatus STOPPING, nothing can move, giving up")
                    return
                routes = self.requiredRoutes(siding)
                self.shortJourney(False, self.loco.block, siding, 'fast', stopIRClear=IRSENSORS[siding.getId()], routes=routes, lock=lock)
            else:
                self.debug("stopped early. Jack Status: " + str(self.getJackStatus()))
        else:
            # This is the 'normal' option - move into a siding
            # self.debug("not stopping early. status :" + str(self.getJackStatus()) + " doesn't equal normal: " + str(NORMAL) + " self.rarity(): " + str(self.loco.rarity()))
            self.debug("moving into sidings")
            siding = None
            while siding is None:
                siding = self.loco.selectSiding(NORTH_SIDINGS, blocking=False)
                if siding is None:
                    if not self.getJackStatus() == NORMAL:
                        self.debug("no available sidings and jack status stopping, giving up")
                        self.loco.setSpeedSetting(0)
                        lock.unlock()
                        return
                    if lock and not lock.empty():
                        # nothing can move out of a siding while I hold the lock
                        self.debug("no sidings available, releasing lock and waiting")
                        self.loco.setSpeedSetting(0)
                        lock.unlock()
                        time.sleep(20)
                    else:
                        # not sure this ever happens
                        time.sleep(5)
                else:
                    if lock and lock.empty():
                        lock.getLock()
            self.debug("selected siding: " + siding.getId())
            if not lock.partial():
                # full lock - might as well set all the routes
                routes = routes + self.requiredRoutes(siding)
            if self.loco.reversible():
                dir = False
            else:
                dir = True
            self.debug("calling shortJourney")
            if speed is None:
                speed = self.loco.speed('off track north', 'medium')
            self.shortJourney(dir, self.loco.block, self.loco.track.nextBlockNorth(self.loco.block), speed, dontStop=True, routes=routes)
            speed = self.loco.speed('north interlink northbound', 'medium')
            self.shortJourney(dir, self.loco.block, 'North Link', speed, dontStop=True)
            if lock.partial():
                routes = self.requiredRoutes(siding)
            else:
                routes = None
            lock.switch()
            self.track.setExitSignalAppearance(GREEN)
            speed = self.loco.speed('north link to sidings', 'fast')
            slowSpeed = self.loco.speed('north sidings entry', 'medium')
            self.shortJourney(dir, self.loco.block, siding, speed, slowSpeed=slowSpeed, stopIRClear=IRSENSORS[siding.getId()], routes=routes)
            lock.unlock()
            lock.logLock()
            self.loco.unselectSiding(siding)
            if not self.loco.reversible():
                self.loco.wrongway = True

        self.loco.status = SIDINGS


    # Moves a loco from any block on the track into a siding
    def moveToASiding(self):
        # get the track we're on
        trak = track.Track.findTrackByBlock(self.tracks, self.loco.block)
        if trak is None:
            return False
        self.loco.track = trak
        self.track = trak
        # work out if we have clear track to either sidings
        clearNorth = None
        nb = self.loco.block
        while clearNorth is None:
            nb = trak.nextBlockNorth(nb)
            if nb is None:
                clearNorth = True
                continue
            if nb.getState() == OCCUPIED:
                clearNorth = False
                continue
        clearSouth = None
        nb = self.loco.block
        while clearSouth is None:
            nb = trak.nextBlockSouth(nb)
            if nb is None:
                clearSouth = True
                continue
            if nb.getState() == OCCUPIED:
                clearSouth = False
                continue
        # if we can't go either way, bale out
        if not clearSouth and not clearNorth:
            return False
        if not self.loco.reversible():
            # check reverse loops 
            if self.track.northbound():
                rl = blocks.getBlock(NORTH_REVERSE_LOOP)
                if rl.getState() != OCCUPIED:
                    self.moveIntoNorthSidings()
                    return True
            else:
                rl = blocks.getBlock(SOUTH_REVERSE_LOOP)
                if rl.getState() != OCCUPIED:
                    self.moveIntoSouthSidings()
                    return True
            return False
        # see if there are sidings free
        nSiding = sSiding = None
        if clearNorth:
            nSiding = self.loco.shortestBlockTrainFits(NORTH_SIDINGS)
        if clearSouth:
            sSiding = self.loco.shortestBlockTrainFits(SOUTH_SIDINGS)
        if nSiding and sSiding:
            if self.freeSidingCount(NORTH_SIDINGS) > self.freeSidingCount(SOUTH_SIDINGS):
                self.moveIntoNorthSidings()
            else:
                self.moveIntoSouthSidings()
            return True
        if nSiding:
            self.moveIntoNorthSidings()
            return True
        if sSiding:
            self.moveIntoSouthSidings()
            return True
        return False



    # moves a train from their current block into the south sidings
    def moveIntoSouthSidings(self, lock=None, speed=None):

        # check we're not in ESTOP status
        if self.getJackStatus() == ESTOP:
            raise EstopError("Estop")

        # wait until the power comes back on
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)

        # deal with locking
        if lock is None or lock.empty():
            if self.loco.throttle.getSpeedSetting() > 0:
                # we need a lock promptly or we must stop
                lock = self.loco.getLockNonBlocking(SOUTH)
            else:
                # we are stationary, we can wait for a lock
                if self.loco.rarity() == 0.0:
                    sleepTime = 5 # no hurry for the lock
                else:
                    sleepTime = None # get getLock() decide
                lock = self.loco.getLock(SOUTH, sleepTime=sleepTime)
        if lock.empty(): # implies we are moving
            # set the signal to red
            self.track.setExitSignalAppearance(RED)
            # bring loco to a halt
            self.loco.graduallyChangeSpeed('slow')
            time.sleep(self.getSlowtime(self.loco.block.getUserName()))
            self.loco.setSpeedSetting(0)
            lock.getLock(SOUTH, SOUTHBOUND, self.loco)
        # one way or another we now have a lock
        self.track.setExitSignalAppearance(GREEN)

        # remove the memory, this journey is finished
        if self.memory is not None:
            m = memories.provideMemory(self.memory)
            m.setValue(0)
        if self.track:
            mem = memories.provideMemory("IMTRACK" + str(self.track.nr) + "LOCO")
            mem.setValue(None)
            mem = memories.provideMemory("IMTRACK" + str(self.track.nr) + "SPEED")
            mem.setValue(None)

        # we are ready to move
        routes = [self.track.exitRoute(self.track.northbound())]
        if not self.loco.reversible():
            b = self.loco.selectReverseLoop(SOUTH_REVERSE_LOOP)
        if not self.loco.reversible() and b is not None:
            # move into reverse loop
            if speed is None:
                speed = self.loco.speed('off track south', 'medium')
            self.shortJourney(True, self.loco.block, 'South Link', speed, dontStop=True, routes=routes)
            if self.loco.trainLength() < 100 or self.loco.fast():
                lock.switch() # slows/stops loco if necessary
                self.track.setExitSignalAppearance(GREEN)
            else:
                self.debug("not switching lock: train is long and slow")
            speed = self.loco.speed('into reverse loop', 'fast')
            self.loco.setSpeedSetting(speed)
            self.reverseLoop(SOUTH_REVERSE_LOOP)
            lock.unlock()
            lock.logLock()
            self.track.setExitSignalAppearance(GREEN)
            self.loco.unselectReverseLoop(SOUTH_REVERSE_LOOP)
        else:
            # 'normal' move into south sidings
            siding = None
            while siding is None:
                # pick a siding
                siding = self.loco.selectSiding(SOUTH_SIDINGS, blocking=False)
                if siding is None:
                    if not self.getJackStatus() == NORMAL:
                        self.debug("no available sidings and jack status stopping, giving up")
                        self.loco.setSpeedSetting(0)
                        lock.unlock()
                        return
                    if lock and not lock.empty():
                        # nothing can move out of a siding while I hold the lock
                        self.debug("no sidings available, releasing lock and waiting")
                        self.loco.setSpeedSetting(0)
                        lock.unlock()
                        time.sleep(20)
                    else:
                        # not sure this ever happens
                        time.sleep(5)
                else:
                    if lock and lock.empty():
                        lock.getLock()
            self.debug("selected siding " + siding.getId())
            if lock.full():
                moreRoutes = self.requiredRoutes(siding)
                self.debug("moveIntoSouthSidings: adding routes: " + ', '.join(moreRoutes))
                routes = routes + moreRoutes
            if speed is None:
                speed = self.loco.speed('track to south link', 'medium')
            dir = True
            self.shortJourney(dir, self.loco.block, "South Link", speed, routes=routes, dontStop=True)
            if lock.partial():
                routes = self.requiredRoutes(siding)
            else:
                routes = None
            lock.switch()
            self.track.setExitSignalAppearance(GREEN)
            if siding.getId() == "FP sidings":
                speed = self.loco.speed('south link to fp sidings', 'fast')
                slowSpeed = self.loco.speed('south sidings entry', 'medium')
                self.shortJourney(dir, self.loco.block, siding, speed, slowSpeed=slowSpeed, routes=routes, stopIRClear=IRSENSORS[siding.getId()])
            else: # normal siding
                if speed is None:
                    # select the speed for the next bit - if a fast loco needs to set routes
                    # we need to go slower
                    if routes is None or not self.loco.fast():
                        speed = self.loco.speed('south link to back passage', 'fast')
                    else:
                        speed = self.loco.speed('south link to back passage slow', 'slow')
                self.shortJourney(dir, self.loco.block, 'Back Passage', speed, routes=routes, dontStop=True)
                speed = self.loco.speed('back passage to south sidings', 'fast')
                slowSpeed = self.loco.speed('south sidings entry', 'medium')
                self.shortJourney(dir, self.loco.block, siding, speed, slowSpeed=slowSpeed, stopIRClear=IRSENSORS[siding.getId()])
            lock.unlock()
            lock.logLock()
            self.loco.unselectSiding(siding)
            if not self.loco.reversible():
                self.loco.wrongway = True
        self.loco.status = SIDINGS

    # Brings a loco out of the south sidings (or reverse loop) onto the
    # layout.
    def leaveSouthSidings(self, endBlock, stop=None, speed=None):

        # wait until the power comes back on
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)

        self.loco.status = MOVING

        # determine direction
        if self.loco.reversible():
            dir = False
        else:
            dir = True

        # Set default stop value if not set by caller
        if stop is None:
            if 'Stopping' in type(self).__name__:
                stop = True
            else:
                stop = False

        # get a lock
        lock = self.loco.getLock(SOUTH)

        # determine the routes we need to set to start moving
        if self.loco.inReverseLoop():
            routes = [self.requiredRoutes(self.loco.block)[1]]
        else:
            routes = self.requiredRoutes(self.loco.block)

        # extra routes we will need eventually
        moreRoutes = self.requiredRoutes(endBlock)

        # if we have a full lock we can set more routes
        self.allRoutesSet = False
        if not lock.partial():
            self.debug("we have a full lock, adding routes for endblock")
            routes = routes + moreRoutes
            self.allRoutesSet = True

        # off we go
        sp = self.loco.speed('south sidings exit', 'fast')
        if self.loco.layoutBlock.getId() != "FP sidings" and not self.loco.inReverseLoop():
            self.debug("we're not in FP sidings or a reverse loop")
            # we're in one of the normal sidings, move out to back pasaage
            if self.allRoutesSet: # implies a full lock
                self.shortJourney(dir, self.loco.block, "Back Passage", sp, routes=routes, dontStop=True)
            else:
                self.shortJourney(dir, self.loco.block, "Back Passage", sp, routes=routes, dontStop=True, lockToUpgrade=lock, upgradeLockRoutes=moreRoutes)
            routes = None
            # set the speed for the next bit
            sp = self.loco.speed('back passage to south link', 'fast')

        # we are now either in back passage, fp sidings, or south reverse loop, next stop: south link
        if lock.partial() and self.loco.fast():
            # slow down a bit
            self.debug("slowing down as we don't have a full lock yet")
            sp = sp / 2.0

        # move to south link
        if self.allRoutesSet:
            self.debug("all routes are set (or in routes), calling shortJourney")
            self.shortJourney(dir, self.loco.block, "South Link", sp, routes=routes, dontStop=True)
        elif lock.partial():
            self.debug("exit routes not set, partial lock, calling shortJourney with lockToUpgrade")
            self.shortJourney(dir, self.loco.block, "South Link", sp, routes=routes, dontStop=True, lockToUpgrade=lock, upgradeLockRoutes=moreRoutes)
        else:
            self.debug("exit routes not set, full lock. How did that happen?")
            self.shortJourney(dir, self.loco.block, "South Link", sp, routes=routes, dontStop=True)

        # we are now at South Link

        # see if we're past the IR sensor at the sidings side of the link
        irs = sensors.getSensor("LS59")
        routeSleepTime = 0
        if irs.knownState == ACTIVE:
            self.debug("south link clear IR sensor is active")
            if lock.partial():
                # we can't switch the lock because our tail is still overhanging the sidings exit,
                # upgrade to full lock instead
                self.debug("attempting non-blocking lock upgrade")
                if lock.upgradeLockNonBlocking(keepOldPartial=True) is False:
                    # we can't upgrade the lock immediately, stop
                    self.debug("didn't get lock, stopping")
                    self.loco.setSpeedSetting(0)
                    # now wait for a lock
                    self.debug('waiting for lock')
                    lock.upgradeLock(keepOldPartial=True)
                    self.debug('got lock')
                    timeStopped = self.loco.timeStopped()
                    if timeStopped < 5:
                        routeSleepTime = 5 - timeStopped
                else:
                    # slow the loco down: there are routes we haven't set
                    # yet and they take a while, meanwhile the loco hasn't stopped
                    self.debug("got lock upgrade")
                    self.debug("stopping loco")
                    self.loco.setSpeedSetting(0)
                    self.debug(lock.status())
                    routeSleepTime = 5
        else: # south link sidings IR sensor is not active (can't see how this happens)
            self.debug('south link clear IR sensor is not active')
            # if the lock is partial we need extra time to set routes
            if lock.partial():
                routeSleepTime = 5
            # update the lock
            lock.switch() # slows/stops loco if necessary

        # we now have a full lock (and we are still at south link, possibly moving)
        # sort out our routes for the  last bit

        if self.allRoutesSet:
            lrs_secs = time.time() - self.lastRouteSetTime
            self.debug("all routes are set, last route was set " + str(lrs_secs) + " secs ago")
            if lrs_secs < 6:
                if self.loco.fast():
                    # all routes are set but very recently - give them time
                    self.debug("slowing loco for a few secs, last routes set recently")
                    sp = self.loco.throttle.getSpeedSetting()
                    self.loco.setSpeedSetting(0)
                    time.sleep(8 - lrs_secs)
                    self.loco.setSpeedSetting(sp)
                else:
                    self.debug("not bothering slowing loco, it's slow already")

        # add later routes if we haven't done so already
        if not self.allRoutesSet:
            self.debug("setting additional routes if necessary")
            routes = self.requiredRoutes(endBlock)
            if routeSleepTime and routeSleepTime > 0:
                w = False
            else:
                w = True
            for r in routes:
                self.setRoute(r, waitTillNotBusy=w)
                if routeSleepTime:
                    self.debug("sleeping for routeSleepTime (" + str(routeSleepTime) +') secs')
                    time.sleep(routeSleepTime)

        # all routes are now set

        # get the speed
        if speed is None:
            sp = self.loco.speed('south link to layout', 'medium')
            # and slowspeed
        else:
            sp = speed
        ssp = self.loco.speed('slow')
        # do this now because it can be a while before we call shortJourney
        self.debug('setting speed early before calling shortJourney: new speed: ' + str(sp))
        self.loco.setSpeedSetting(sp)


        # if the sidings IR sensor is still active, wait for it before we release the lock
        if irs.knownState == ACTIVE:
            self.debug("waiting for south link clear IR sensor to go inactive before partially releasing lock")
            if self.loco.throttle.getSpeedSetting() == 0:
                self.debug('get loco moving (currently stationary)')
                self.loco.setSpeedSetting(sp)
            self.waitChange([irs])
            self.debug('IR sensor clear, partially releasing lock')
            lock.unlock(partialUnlock=True)


        # check if we are already in the endblock, this can happen with long trains
        b, s = self.convertToLayoutBlockAndSensor(endBlock)
        if b.getBlock().getState() == OCCUPIED:
            ignoreOccupiedEndlock = True
        else:
            ignoreOccupiedEndlock = False

        # complete the move
        if stop:
            self.shortJourney(dir, self.loco.block, endBlock, sp, slowSpeed=ssp, lock=lock, lockSensor="LS60", ignoreOccupiedEndBlock=ignoreOccupiedEndlock)
            self.waitAtPlatform()
        else:
            self.shortJourney(dir, self.loco.block, endBlock, sp, lock=lock, dontStop=True, lockSensor="LS60", ignoreOccupiedEndBlock=ignoreOccupiedEndlock)
        self.debug('leaveSouthSidings done')
        # phew

    # Brings a loco out of the south sidings (or reverse loop) onto the
    # layout.
    def leaveNorthSidings(self, endBlock, stop=None, speed=None):
        # wait until the power comes back on
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)

        self.loco.status = MOVING
        dir = True
        # Set default stop value if not set by caller
        if stop is None:
            if 'Stopping' in type(self).__name__:
                stop = True
            else:
                stop = False
        # get a lock
        lock = self.loco.getLock(NORTH)
        if self.loco.block.getUserName() != "North Link":
            # determine the routes we need to set to start moving
            if self.loco.inReverseLoop():
                routes = [self.requiredRoutes(self.loco.block)[1]]
            else:
                routes = self.requiredRoutes(self.loco.block)
            # if we have a full lock we can set more routes
            if not lock.partial():
                routes = routes + self.requiredRoutes(endBlock)
            # get the loco speed
            sp = self.loco.speed('north sidings exit', 'fast')
            self.shortJourney(dir, self.loco.block, "North Link", sp, routes=routes, dontStop=True)
            # update the lock
            lock.switch() # stops loco if necessary
            # add later routes if we haven't done so already
            if lock.partial():
                routes = self.requiredRoutes(endBlock)
            else:
                routes = None
        else:
            # we're on the north link having stopped early on the previous journey
            routes = self.requiredRoutes(endBlock)
            lock.unlock(partialUnlock=True)
        # get the speed
        sp = self.loco.speed('north interlink southbound', 'medium')
        # move to the fast/slow link
        if self.loco.track.nr > 2:
            eb = "Nth Fast Link"
        else:
            eb = "Nth Slow Link"
        self.shortJourney(dir, self.loco.block, eb, sp, routes=routes, dontStop=True)
        # new speed
        if speed is None:
            sp = self.loco.speed('north link to layout', 'medium')
        else:
            sp = speed
        # and slowspeed
        ssp = self.loco.speed('slow')
        # complete the move
        routes = [] # experimental
        if stop:
            self.shortJourney(dir, self.loco.block, endBlock, sp, slowSpeed=ssp, lock=lock, routes=routes, lockSensor="LS64")
            self.waitAtPlatform()
        else:
            self.shortJourney(dir, self.loco.block, endBlock, sp, lock=lock, routes=routes, dontStop=True, lockSensor="LS64")
        self.debug('leaveNorthSidings done')

    def handle(self):
        try:
            self.go()
        except EstopError:
            if self.loco:
                self.loco.emergencyStop()
            debug("Exiting on Estop")
            return false


        

