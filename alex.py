import jmri
import time

from jmri_bindings import *
from myroutes import ROUTEMAP


class Alex(jmri.jmrit.automat.AbstractAutomaton):

    # init() is called exactly once at the beginning to do
    # any necessary configuration.
    def init(self):
        # legacy block definitions
        self.sthSidings = sensors.provideSensor("34")
        self.sthSidingsClearIR = sensors.provideSensor("25")
        self.fpkP4 = sensors.provideSensor("22")
        self.aapP1 = sensors.provideSensor("4")
        self.aapP2 = sensors.provideSensor("2")
        self.aapP3 = sensors.provideSensor("3")
        self.aapP4 = sensors.provideSensor("1")
        self.nsgP2 = sensors.provideSensor("8")
        self.nsgP1 = sensors.provideSensor("7")
        self.nthSiding1 = sensors.provideSensor("37")
        self.nthSiding1ClearIR = sensors.provideSensor("27")
        self.nthSiding2ClearIR = sensors.provideSensor("28")
        self.fpkP2 = sensors.provideSensor("21")
        self.fpkP1 = sensors.provideSensor("24")
        self.fpkP3 = sensors.provideSensor("23")
        self.fpkP8 = sensors.provideSensor("36")
        self.nthReverseLoop = sensors.provideSensor("19")
        self.sthReverseLoop = sensors.provideSensor("35")
        self.palP1 = sensors.provideSensor("6")
        self.palP2 = sensors.provideSensor("5")
        self.sthLink = sensors.provideSensor("33")
        self.platformWaitTimeMsecs = 10000
        self.backPassage = sensors.provideSensor("17")
        self.routesToSetForNextJourney = []
        return
    
    # Get's a 'lock' on a memory variable. It sets the variable
    # to the loco number but only if the value is blank. If 
    # it's already got a value then we wait for a while to see
    # if it clears, otherwise we give up.
    def getLock(self, mem, loco = None):
        if loco is None:
            loco = self.loco
        lock = False
        tries = 0
        while lock is not True:
            print loco, "getting lock on", mem
            value = memories.getMemory(mem).getValue()
            if value == str(loco):
                return mem
            if value is None or value == '':
                memories.getMemory(mem).setValue(str(loco))
                time.sleep(1)
                value = memories.getMemory(mem).getValue()
                if value == str(loco):
                    lock = True
                else:
                    # race condition and we lost
                    tries += 1
                    if tries < 20:
                        print loco, "new memory setting did not stick, trying again"
                        time.sleep(5)
                    else:
                        print loco, "giving op on lock"
                        return False

            else:
                # link track is busy
                tries += 1
                if tries < 40:
                    print loco, "track is locked, waiting ..."
                    time.sleep(5)
                else:
                    print loco, "giving up on lock"
                    return False
            time.sleep(5)
        return mem


    # Attempts to get a lock and returns immediately whether or
    # not the attempt was successful. No race condition testing
    # is done, the calling function can do that with checkLock()
    def getLockNonBlocking(self, mem, loco):
        lock = False
        print loco, "getting non-blocking lock on", mem
        value = memories.getMemory(mem).getValue()
        if value == str(loco):
            return mem
        if value is None or value == '':
            memories.getMemory(mem).setValue(str(loco))
            return mem
        print loco, "failed to get non-blocking lock on", mem
        return False

    # Returns true if the loco supplied has a lock on the
    # mem supplied, false otherwise
    def checkLock(self, mem, loco):
        memory = memories.getMemory(mem)
        if memory is None:
            memory = memories.newMemory(mem)
        if memory is None:
            print loco, "could not create memory called", mem, "giving up"
            raise RuntimeError('coulnd not create new memory')
        if memory and memory.getValue() == str(loco):
            return True
        print loco, "does not have lock on ", mem
        return False

    # Does not actually set a route. Adds the route name
    # to a list which will be set next time a journey
    # is undertaken
    def setMyRoute(self, route):
        self.routesToSetForNextJourney.append(route)

    # sets (triggers) a route
    def setRoute(self, route, sleeptime=5):
        print self.loco, 'setting route', route
        r = routes.getRoute(route)
        if r is None:
            raise RuntimeError("no such route: " + route)
        r.activateRoute()
        r.setRoute()
        if sleeptime is not None and sleeptime > 0:
            time.sleep(sleeptime)

    # removes a lock
    def unlock(self, mem, loco = None):
        if loco is None:
            loco = self.loco
        print loco, "unlocking", mem
        memories.getMemory(mem).setValue(None)

    # Calculates the routes required to connect the siding using
    # a dictionary (aka hash) specified in an external file
    def requiredRoutes(self, siding):
        if siding in ROUTEMAP:
            return ROUTEMAP[siding]
        return siding

    # Brings the locomotive controlled by the supplied throttle
    # to a gradual halt by reducing the speed setting over time seconds
    def gradualHalt(self, throttle, time = 5, granularity = 1):
        if time <= granularity:
            print self.loco, "stopping train"
            throttle.setSpeedSetting(0)
            self.waitMsec(250)
            throttle.setSpeedSetting(0)
            return
        if granularity < 0.25:
            granularity = 0.25 # avoid too many loconet messages
        print self.loco, "bringing train to halt over", time, "secs"
        speed = throttle.getSpeedSetting()
        times = time / granularity
        speedDiff = speed / times
        print self.loco, "speed:", speed, "times:", times, "speedDiff:", speedDiff
        while True:
            speed = throttle.getSpeedSetting()
            newSpeed = speed - speedDiff
            if newSpeed < 0:
                newSpeed = 0
            print "    gradual halt setting speed", newSpeed
            throttle.setSpeedSetting(newSpeed)
            if newSpeed == 0:
                return


    # Gets a train from startBlock to endBlock and optionally slows it down
    # and stops it there. Tries to update block occupancy memory values.
    def shortJourney(self, throttle, direction, startBlock, endBlock, 
                     normalSpeed, slowSpeed, slowTime=0,
                     stopIRClear=None, checkSensor=None, routes=None, lock=None):

        # get the loco number for console messages
        loco = throttle.getLocoAddress().getNumber()
        
        # are we moving
        if throttle.getSpeedSetting() > 0:
            moving = True
        else:
            moving = False

        print loco, "called shortJourney()"

        # determine what startBlock is (string name of block, the block itself, or the sensor of the block)
        # and get the sensor one way or the other
        if type(startBlock) == str:
            sb = layoutblocks.getLayoutBlock(startBlock)
            if sb is None:
                raise RuntimeError("no such block: " + startBlock)
            startBlock = sb
            startBlockSensor = sb.getOccupancySensor()
        elif type(startBlock) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            # startBlock is a LayoutBlock
            startBlockSensor = startBlock.getOccupancySensor()
        else:
            # startBlock is the sensor
            startBlockSensor = startBlock
            startBlock = layoutblocks.getBlockWithSensorAssigned(startBlockSensor)

        # and again with endBlock
        if type(endBlock) == str:
            eb = layoutblocks.getLayoutBlock(endBlock)
            if eb is None:
                raise RuntimeError("no such block: " + endBlock)
            endBlock = eb
            endBlockSensor = eb.getOccupancySensor()
        elif type(endBlock) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            endBlockSensor = endBlock.getOccupancySensor()
        else:
            # it's a sensor
            endBlockSensor = endBlock
            endBlock = layoutblocks.getBlockWithSensorAssigned(endBlockSensor)
            if endBlock is None:
                print "end block sensor provided is not assigned to a layout block"
                raise RuntimeError("end block sensor provided is not assigned to a layout block")

        # check if we know where we are if the startblock is not occupied
        if startBlockSensor.knownState != ACTIVE:
            print loco, "start block is not occupied"
            if self.knownLocation is None:
                print "and no known location,", loco, "exiting"
                return False
            if self.knownLocation != startBlock:
                print "and known location does not match start block,", loco, "exiting"
                return False

        # check we are ok to start moving (ie. the target block is free)
        ok_to_go = False
        tries = 0
        while not ok_to_go:
            if endBlockSensor.knownState == ACTIVE:
                print loco, "endblock is occupied"
                if lock:
                    print loco, "relinquising lock"
                    if self.checkLock(lock, loco):
                        self.unlock(lock, loco)
                if moving:
                    print loco, "stopping"
                    throttle.setSpeedSetting(0)
                if tries < 40:
                    print loco, "waiting..."
                    time.sleep(5)
                    tries += 1
                else:
                    print loco, "giving up"
                    return False
            else:
                ok_to_go = True

        # if we are already moving set the new throttle setting
        # before we set routes or we might get to the next turnout
        # too soon, too fast
        if moving:
            print loco, "we are already moving, setting normal speed:", normalSpeed
            throttle.setSpeedSetting(normalSpeed)
            self.waitMsec(250)
            throttle.setSpeedSetting(normalSpeed)
            
        # If we have a lock specified, check we've got it
        if lock:
            if not self.checkLock(lock, loco):
                lock = self.getLock(lock, loco)
                if lock is False:
                    print loco, "failed to get lock on", lock, "giving up"
                    return False
            
        # Set Routes. These can be provided by the routes
        # argument or stored up in a list by previous calls
        # to setMyRoute(), or both.

        if routes is not None:
            for r in routes:
                self.setRoute(r)
        for r in self.routesToSetForNextJourney:
            self.setRoute(r)
        if len(routes) + len(self.routesToSetForNextJourney) > 1:
            time.sleep(5)
        self.routesToSetForNextJourney = []
        
        # if we are stationary, and the current direction is different
        # from the direction requested, set direction
        if not moving and throttle.getIsForward() != direction:
            if direction is True:
                dir = 'forward'
            else:
                dir = 'reverse'
            print loco, "setting direction to", dir
            throttle.setIsForward(direction) 
            self.waitMsec(250)
            throttle.setIsForward(direction) 
            self.waitMsec(500)
        
        # set throttle position if we're not already moving (if we
        # are moving we set the throttle earlier
        if not moving:
            print loco, "Setting normal Speed", normalSpeed
            throttle.setSpeedSetting(normalSpeed)
            # sometimes the first instruction gets lost
            self.waitMsec(250)
            throttle.setSpeedSetting(normalSpeed)

        # wait for a sensor uproute to change
        print loco, "waiting for block", endBlock.userName, "to becoming active"
        if checkSensor:
            # we have an 'overrun' sensor to check as well as the
            # one we expect to change
            self.waitChanges([endBlockSensor, checkSensor])
            if endBlockSensor.knownState != ACTIVE and checkSensor.knownState == ACTIVE:
                # loco has overrun
                print loco, "has overrun, aborting"
                throttle.setSpeedSetting(-1)
                return False
        else:
            self.waitSensorActive(endBlockSensor)
        print loco, "block", endBlock.userName, "is active"

        # if there was a lock specified it means the calling method
        # wants us to release it now
        if lock != None:
            self.unlock(lock)


        # set the memory value in the new occupied block
        if endBlock:
            mem = memories.getMemory(endBlock.userName)
            if mem is None:
                mem = memories.newMemory(endBlock.userName)
            if mem:
                print loco, "setting value of newly occupied block", endBlock.userName, "to", loco
                mem.setValue(loco)
            else:
                print loco, "couldn't find memory called ", endBlock.userName, "and couldn't create a new one"
 
        # slow the loco down in preperation for a stop (if slowSpeed is set)
        if slowSpeed < 0:
            print loco, "continuing ... "
            # do nothing
        else:
            if slowSpeed > 0:
                # slow train to 'slowspeed'
                print loco, "endBlock occupied, setting slowspeed", slowSpeed
                throttle.setSpeedSetting(slowSpeed)
            if stopIRClear:
                # wait till the IR sensor is clear
                if stopIRClear.knownState != ACTIVE:
                    sn = stopIRClear.userName
                    if sn is None:
                        sn = stopIRClear.systemName
                    print loco, "waiting for IR sensor", sn ,"to be active"
                    self.waitSensorActive(stopIRClear)
                print loco, "waiting for IR sensor to be inactive"
                self.waitSensorInactive(stopIRClear)
            else:
                # there is no IR sensor to wait for, wait the specified time
                print loco, "no IR sensor, waiting for specified delay:", slowTime / 1000, 'secs'
                self.waitMsec(slowTime)
        
            # stop the train
            print "stopping loco", loco
            throttle.setSpeedSetting(0)
            self.waitMsec(500)
            throttle.setSpeedSetting(0)

        # we know where we are now
        self.knownLocation = endBlock
        
        print loco, "shortJourney() returning"
        return True
                
    def handle(self):
        pass

        

