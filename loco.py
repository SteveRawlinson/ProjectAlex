import jmri
import time
from jmri_bindings import *
from myroutes import *
import util
import lock

DEBUG = True

class Loco(util.Util):
    
    def __init__(self, dccAddr):
        if dccAddr is not None: self.dccAddr = int(dccAddr)
        self._trainLength = None
        self._rosterEntry = None
        self._rarity = None
        self.roster = jmri.jmrit.roster.Roster.instance()
        self.block = None
        self.layoutBlock = None
        self.status = SIDINGS
        self._longAddr = None
        self._reversible = None
        #self._highSpeed = None
        self._brclass = None
        self._passenger = None
        self._fast = None
        self.throttle = None
        self.wrongway = False
        self.track = None
        self._canGoFast = None
        self._canGoSlow = None
        self._freight = None
        self._decoderFamily = None
        self.stopTime = time.time()

    def emergencyStop(self):
        self.debug("emergency stop")
        self.throttle.setSpeedSetting(-1)
        time.sleep(0.1)
        self.throttle.setSpeedSetting(0)
        time.sleep(0.1)
        self.throttle.setSpeedSetting(-1)
        self.stopTime = time.time()

    def setSpeedSetting(self, speed):
        slot = self.throttle.getLocoNetSlot()
        if slot is None:
            print "***************************** Throttle for loco ", self.nameAndAddress(), "has no slot ***********************************"
        if type(speed) == str or type(speed) == unicode:
            speed = self.speed(speed)
        self.debug("setSpeedSetting: " + str(speed) + " slot status: " + LN_SLOT_STATUS[slot.slotStatus()] + " (" + str(slot.slotStatus()) + ")")
        self.throttle.setSpeedSettingAgain(speed)
        if self.track:
            mem = memories.provideMemory("IMTRACK" + str(self.track.nr) + "SPEED")
            mem.setValue(str(round(speed, 2)))
        if float(speed) ==  0.0:
            # make sure the message gets through - wait a bit
            time.sleep(0.1)
#            # set the speed to the minimum above zero
#            self.throttle.setSpeedSetting(self.throttle.getSpeedIncrement())
            # set zero again
#            time.sleep(0.05)
            self.throttle.setSpeedSettingAgain(speed)
            time.sleep(0.2)
            self.throttle.setSpeedSettingAgain(speed)
            self.stopTime = time.time()

    def timeStopped(self):
        if self.throttle.getSpeedSetting() != 0.0:
            return 0
        return time.time() - self.stopTime

    # returns the smallest number that will actually have any impact on
    # the speed if it's used to change the speed. Differs depending on
    # the number of speed steps the chip will handle
    def minimumSpeedIncrement(self):
        return self.throttle.getSpeedIncrement()

    # send a reminder of the speed the loco is supposed to be doing
    def repeatSpeedMessage(self, speed):
        if type(speed) == str or type(speed) == unicode:
            speed = self.speed(speed)
        self.throttle.setSpeedSettingAgain(speed - self.minimumSpeedIncrement())
        time.sleep(0.2)
        self.throttle.setSpeedSettingAgain(speed)

    # Changes the loco's speed setting in 0.5 second steps over
    # the duration. So, if duration is 2 secs then there are 5 steps 0.5
    # seconds apart.
    def graduallyChangeSpeed(self, newSpeed, duration = 2):
        if not type(newSpeed) == float:
            newSpeed = self.speed(newSpeed)
        speed = self.throttle.getSpeedSetting()
        gradCount = float(duration) * 2 + 1
        grad = (newSpeed - speed) / gradCount
        s = speed + grad
        for i in range(int(gradCount)):
            self.throttle.setSpeedSetting(s)
            if self.track:
                m = memories.provideMemory("IMTRACK" + str(self.track.nr) + "SPEED")
                m.setValue(str(round(s, 2)))
            s += grad
            if i != gradCount - 1:
                time.sleep(0.5)
        if float(newSpeed) == 0.0:
            time.sleep(0.5)
            self.throttle.setSpeedSetting(-1)

    def forward(self):
        self.throttle.setIsForward(True)
        time.sleep(0.2)
        self.throttle.setIsForward(True)

    def reverse(self):
        self.throttle.setIsForward(False)
        time.sleep(0.2)
        self.throttle.setIsForward(False)


    # def debug(self, message):
    #     if DEBUG:
    #         print "Loco: ", str(self.dccAddr) + ': ' + message

    # Returns the roster ID (ie. the name)
    def name(self):
        return self.rosterEntry().getId()

    def nameAndAddress(self):
        return self.name() + " (" + str(self.dccAddr) + ")"

    # Returns the length of the train, as recorded in the attribute
    # 'length' in the loco roster.
    def trainLength(self):
        if self._trainLength is None:
            self._trainLength = float(self.rosterEntry().getAttribute('length'))
        return self._trainLength

    # Returns the float 'rarity' which is set in the JMRI roster
    # entry, or zero (the default). Zero raroty means it's a common
    # train, seen often. Higher rarity means the loco doesn't get
    # out much.
    def rarity(self):
        if self._rarity is None:
            r = self.rosterEntry().getAttribute('rarity')
            if type(r) == str or type(r) == unicode:
                self._rarity = float(r)
            else:
                self._rarity = 0 # default
        return self._rarity

    # Returns the BR Class of locomotive, if set in the
    # JMRI roster entry
    def brclass(self):
        if self._brclass is None:
            c = self.rosterEntry().getAttribute('class')
            self._brclass = c
        return self._brclass

    # A boolean set in the JMRI roster entry, default is False
    # def highSpeed(self):
    #     if self._highSpeed is None:
    #         r = self.rosterEntry().getAttribute('highspeed')
    #         if r is None:
    #             self._highSpeed = False  # this is the default
    #         if r == 'true':
    #             self._highSpeed = True
    #         else:
    #             self._highSpeed = False
    #     return self._highSpeed

    # Returns True if the roster entry is a passenger loco
    def passenger(self):
        if self._passenger is None:
            r = self.rosterEntry().getAttribute('passenger')
            if r is None:
                self._passenger = False  # this is the default
            if r == 'true':
                self._passenger = True
            else:
                self._passenger = False
        return self._passenger

    def freight(self):
        if self._freight is None:
            r = self.rosterEntry().getAttribute('freight')
            if r is None:
                self._freight = False  # this is the default
            if r == 'true':
                self._freight = True
            else:
                self._freight = False
        return self._freight

    # Returns True if this train can move in both directions, False otherwise
    def reversible(self):
        if self._reversible is None:
            r = self.rosterEntry().getAttribute('reversible')
            if r is None:
                self._reversible = True # this is the default
            elif r == 'true':
                self._reversible = True
            else:
                self._reversible = False
        return self._reversible

    def fast(self):
        if self._fast is None:
            r = self.rosterEntry().getAttribute('fast')
            if r is None:
                self._fast = False  # this is the default
            if r == 'true':
                self._fast = True
            else:
                self._fast = False
        return self._fast

    def canGoFast(self):
        if self._canGoFast is None:
            r = self.rosterEntry().getAttribute('canGoFast')
            if r is None:
                self._canGoFast = False
            if r == 'true':
                self._canGoFast = True
            else:
                self._canGoFast = False
        return self._canGoFast

    def canGoSlow(self):
        if self._canGoSlow is None:
            r = self.rosterEntry().getAttribute('canGoSlow')
            if r is None:
                self._canGoSlow = False
            if r == 'true':
                self._canGoSlow = True
            else:
                self._canGoSlow = False
        return self._canGoSlow

    # Returns true if this is a slow passenger train (eg. class 150)
    def commuter(self):
        if self.fast() is False and self.passenger() is True:
            return True
        return False

    # Returns the roster entry for the current loco
    def rosterEntry(self):
        if self._rosterEntry is None:
            # # roster_entries = self.roster.getEntriesByDccAddress(str(self.dccAddr))
            roster_entries = self.roster.getEntriesMatchingCriteria(None, None, str(self.dccAddr),
                                                                    None, None, None, None, None)
            if len(roster_entries) == 0:
                raise RuntimeError("no Roster Entry for address", str(self.dccAddr))
            self._rosterEntry = roster_entries[0]

        return self._rosterEntry

    def longAddr(self):
        if self._longAddr is None:
            re = self.rosterEntry()
            self._longAddr = re.isLongAddress()
        return self._longAddr

    def decoderFamily(self):
        if self._decoderFamily is None:
            self._decoderFamily = self.rosterEntry().getDecoderFamily()
        return self._decoderFamily

    # Returns True if the block is longer than the current train.
    # The length of the train is determined by checking the 
    # attribute 'length' in the loco roster.
    def willFitInBlock(self, block):
        if block.getBlock().getLengthCm() > self.trainLength():
            #self.debug("train will fit in block " + block.getId())
            return True
        #self.debug("train won't fit in block " + block.getId() + ", block is " + str(block.getBlock().getLengthCm()) + " cms long, trains is " + str(self.trainLength()))
        return False

    # Takes an array of block names and returns the shortest empty block
    # that the current loco will fit in. Returns a LayoutBlock.
    def shortestBlockTrainFits(self, blocklist):
        sbtf = None
        for b in blocklist:
            block = layoutblocks.getLayoutBlock(b)
            mem = memories.getMemory("IMSIDING" + b.upper())
            sens = block.getOccupancySensor()
            if mem is None:
                self.log("  considering block " + b + " state: " + str(block.getState()) + " mem value: no such memory IMSIDING" + b.upper())
            else:
                self.log("  considering block " + b + " state: " + str(block.getState()) + " sensor: " + sens.getDisplayName() + " sensor state: " + str(sens.getKnownState()) +
                         " mem value: " + str(mem.getValue()) + " length: " + str(block.getBlock().getLengthCm()))
            if block is None:
                self.debug("no such block: " + b)
                self.log("no such block: " + b)
            elif block.getState() == OCCUPIED:
                self.log("  block " + b + " is occupied")
            elif mem is not None and mem.getValue() == "selected":
                self.log("block " + b + " is already selected by another loco")
            elif sbtf is None or block.getBlock().getLengthCm() < sbtf.getBlock().getLengthCm():
                if self.willFitInBlock(block):
                    self.log("  block is best match thus far")
                    sbtf = block
                elif sbtf is None:
                    self.log("  block isn't big enough for train")
                else:
                    self.log("  block " + b + " is not shorter than selected block (" + str(block.getBlock().getLengthCm()) + " > " + str(sbtf.getBlock().getLengthCm()) + ')')
        if sbtf is None:
            self.log("no available sidings")
        return sbtf

    # Takes an array of block names and returns the shortest empty block
    # that the current loco will fit in. If no such blocks are available
    # it waits for 5 minutes.
    def shortestBlockTrainFitsBlocking(self, blocklist):
        start = time.time()
        sbtf = self.shortestBlockTrainFits(blocklist)
        while sbtf is None:
            if time.time() - start > 60 * 5:
                raise RuntimeError("timeout waiting for a free siding")
            time.sleep(5)
            sbtf = self.shortestBlockTrainFits(blocklist)
        return sbtf

    # Selects a siding from a list and sets a memory value to prevent
    # another loco selecting the same one. The object returned is type
    # LayoutBlock
    def selectSiding(self, sidings, blocking=True):
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)
        self.log("selecting siding for loco length " + str(self.trainLength()))
        if blocking:
            siding = self.shortestBlockTrainFitsBlocking(sidings)
        else:
            siding = self.shortestBlockTrainFits(sidings)
            if siding is None:
                return None
        mem = memories.provideMemory(self.sidingMemoryName(siding))
        mem.setValue("selected")
        self.log("  selected siding " + siding.getId() + " memory: " + mem.getSystemName())
        return siding

    # Removes the memory which reserves the siding.
    def unselectSiding(self, siding):
        mem = memories.provideMemory(self.sidingMemoryName(siding))
        self.log("unselecting siding " + mem.getSystemName())
        mem.setValue(None)

    # unselect a bunch of sidings
    @classmethod
    def unselectSidings(cls, sidings):
        for siding in sidings:
            Loco(None).unselectSiding(siding)


    # Checks if the reverse loop (name) supplied is occupied
    # or already selected, returns None if so, or the block
    # if it's available
    def selectReverseLoop(self, loop):
        while powermanager.getPower() == jmri.PowerManager.OFF:
            time.sleep(1)
        b = blocks.getBlock(loop)
        if b is None:
            raise RuntimeError("no such block: " + loop)
        if b.getState() == OCCUPIED:
            self.log("  reverse loop " + loop + " is occupied")
            return None
        mem = memories.provideMemory("IMLOOP" + loop.upper())
        if mem.getValue() is not None:
            self.log("  reverse loop " + loop + " is selected by " + str(mem.getValue()))
            return None
        mem.setValue(self.dccAddr)
        self.log("  reverse loop " + loop + " is available")
        return b

    def unselectReverseLoop(self, loop):
        mem = memories.provideMemory("IMLOOP" + loop.upper())
        mem.setValue(None)

    @classmethod
    def unselectReverseLoops(cls, loops):
        for loop in loops:
            Loco(None).unselectReverseLoop(loop)

    # returns True if the loco is in a reverse loop
    def inReverseLoop(self):
        if self.block is None:
            return None
        if self.block.getUserName() == NORTH_REVERSE_LOOP or self.block.getUserName() == SOUTH_REVERSE_LOOP:
            return True
        return False

    # Returns the list of layout block(s) I'm in
    def myLayoutBlocks(self):
        # return layoutblocks.getLayoutBlocksOccupiedByRosterEntry(self.rosterEntry())
        blockList = []
        for name in blocks.getSystemNameList():
            b = blocks.getBySystemName(name)
            if b.getUserName() is not None:
                lob = layoutblocks.getLayoutBlock(b.getUserName())
            else:
                lob = None
            if lob is not None:
                if type(b.getValue()) == jmri.jmrit.roster.RosterEntry and b.getValue() == self.rosterEntry():
                    blockList.append(lob)
                elif b.getValue() == self.rosterEntry().getId() or b.getValue() == str(self.dccAddr):
                    blockList.append(lob)
        return blockList

    # Sets the instance variable 'block' using information
    # from the layout
    def initBlock(self):
        lblocks = self.myLayoutBlocks()
        if len(lblocks) == 0:
            self.block = None
        elif len(lblocks) == 1:
            if lblocks[0].getOccupancy() == OCCUPIED:
                self.setBlock(lblocks[0].getBlock())
        else:
            # technically a loco can be in more than one block but in
            # practice at startup it's much more likely that multiple
            # blocks means there's an error. Reset all block values.
            self.block = None
            for lb in lblocks:
                b = lb.getBlock()
                b.setValue(None)


        if DEBUG:
            if self.block is None:
                self.debug("loco " + str(self.dccAddr) + " block: None")
            elif type(self.block) == jmri.Block:
                self.debug("loco " + str(self.dccAddr) + " block: " + self.block.getUserName())
            else:
                raise RuntimeError("loco " + str(self.dccAddr) + " block has unknown type: " + type(self.block).__name__)
        return self.block

    # Sets this loco's block to b (if it's a block)
    # or to b's block (if it's a layoutblock) or to
    # the block whose name is b (if it's a string).
    # Also sets the block's value to the loco's
    # dcc address.
    def setBlock(self, b):
        #self.debug("type: " + type(b).__name__)
        lblk = None
        if type(b) == str or type(b) == unicode:
            lblk = layoutblocks.getLayoutBlock(b)
            if lblk is None:
                raise RuntimeError("no such layoutblock: " + b)
            blk = lblk.getBlock()
        elif type(b) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            lblk = b
            blk = b.getBlock()
        else:
            blk = b
        # remove value on old block
        if self.block:
            self.debug("removing value on old block " + self.block.getDisplayName())
            self.block.setValue(None)
            #self.debug("set block " + self.block.getUserName() + " to None. Value now: " + str(self.block.getValue()))
            mem = memories.getMemory(self.block.getUserName())
            if mem is not None:
                mem.setValue(None)
                #self.debug("set memory " + self.block.getUserName() + " to None. Value now: " + str(mem.getValue()))
        # set new block
        self.block = blk
        if lblk is not None:
            self.layoutBlock = lblk
        else:
            self.layoutBlock = layoutblocks.getLayoutBlock(blk.getUserName())
        blk.setValue(str(self.dccAddr))
        mem = memories.getMemory("Siding " + blk.getUserName())
        if mem is not None and mem.getValue() == str(self.dccAddr):
            # The block we are now in is a siding we reserved. Remove the reservation.
            mem.setValue(None)
        #self.debug("new block value: " + blk.getValue())

    def setLayoutBlock(self, b):
        self.setBlock(b)

    # Returns True if self is in the north sidings
    def northSidings(self):
        blockname = self.block.getUserName()
        #self.debug("northSidings: my status is SIDINGS, my blockname is " + blockname + " type " + type(blockname).__name__)
        if blockname in NORTH_SIDINGS or blockname == NORTH_REVERSE_LOOP or blockname == "North Link":
            return True
        return False

    # returns True if self is in the South Sidings
    def southSidings(self):
        if self.block.getUserName() in SOUTH_SIDINGS or self.block.getUserName() == SOUTH_REVERSE_LOOP:
            return True
        return False

    def active(self):
        return self.status == MOVING

    def moving(self):
        return self.status == MOVING

    def idle(self):
        return self.status == SIDINGS

    # Returns a floating point number between 0 and 1 which it looks
    # up in the SPEEDMAP constant. It first looks for the dcc address
    # as the key, and then for the class. If it doesn't find it in
    # either place it then looks for the 'fallback' option instead.
    # If it gets a string it searches again using the string as the
    # key.
    def speed(self, speed, fallback = 'medium'):
        if speed == 'stop': return 0.0
        if speed == 'estop': return -1
        sp = speed
        while type(sp) != float:
            sp = self.getSpeed(sp, fallback)
        self.debug("getting speed: " + speed + ":  " + str(sp))
        return sp

    # does the donkey work for self.speed()
    def getSpeed(self, speed, fallback = 'medium'):
        sp = None
        if self.dccAddr in SPEEDMAP:
            if speed in SPEEDMAP[self.dccAddr]:
                sp = SPEEDMAP[self.dccAddr][speed]
        if sp is None and self.brclass() is not None:
            k = "class" + str(self.brclass())
            if k in SPEEDMAP:
                if speed in SPEEDMAP[k]:
                    sp = SPEEDMAP[k][speed]
                if sp is None and fallback in SPEEDMAP[k]:
                    return SPEEDMAP[k][fallback]
        if sp is None and self.dccAddr in SPEEDMAP:
            if fallback in SPEEDMAP[self.dccAddr]:
                sp = SPEEDMAP[self.dccAddr][fallback]
        if sp is None and self.brclass() is not None:
            k = "class" + str(self.brclass())
            if k in SPEEDMAP:
                if fallback in SPEEDMAP[k]:
                    sp = SPEEDMAP[k][fallback]
        if type(sp) == float and sp > 1.0:
            self.emergencyStop()
            raise RuntimeError("speed " + str(sp) + " is too high")
        return sp

    # Returns the hash of slowtimes for this loco
    def slowTimes(self):
        if self.dccAddr in SLOWTIMEMAP:
            return SLOWTIMEMAP[self.dccAddr]
        k = "class" + str(self.brclass())
        if k in SLOWTIMEMAP:
            return SLOWTIMEMAP[k]
        return None

    # Gets the slowtime - the number of seconds to
    # move at slowSpeed before coming to a halt at a platform.
    # Slowtimes are defined in myroutes. If there is no
    # slowtime defined for the loco at the destination
    # it returns a default of 1.
    def getSlowtime(self, destination):
        st = self.slowTimes()
        if st is not None:
            if destination in st:
                return st[destination]
        self.debug("**************************** can't find slowtime for " + self.nameAndAddress() + " at " + destination + "******************************")
        return 1


    # String representation of my direction, ie Nth2Sth or Sth2Nth
    def dir(self):
        if self.track is None:
            return None
        return self.track.dir()

    # Returns the loco object from the array locos with
    # the matching DCC addr
    @classmethod
    def getLocoByAddr(self, addr, locos):
        addr = int(addr)
        for l in locos:
            if l.dccAddr == addr:
                return l
        return None

    # Attempts to get a lock but doesn't wait if it's not
    # available
    def getLockNonBlocking(self, end):
        if self.track.northbound():
            dir = NORTH
        else:
            dir = SOUTH
        l = lock.Lock()
        l.getLockNonBlocking(end, dir, self)
        if l.empty():
            self.debug("failed to get lock (non-blocking) returning empty lock")
        self.debug("loco.getLockNonBlocking: got lock: " + l.status())
        return l

    # Gets a lock. See lock.py for details
    def getLock(self, end, sleepTime=None):
        if self.track.northbound():
            self.debug(self.track.name() + " is northbound")
            dir = NORTHBOUND
        else:
            self.debug(self.track.name() + " is southbound")
            dir = SOUTHBOUND
        if end == NORTH:
            end_s = 'North'
        else:
            end_s = 'South'
        self.debug("getting lock on " + end_s + " link (end = " + str(end) + ")")
        l = lock.Lock()
        l.getLock(end=end, direction=dir, loc=self, sleepTime=sleepTime)
        return l

    # On decoders that support disabling momentum, set the
    # appropriate function to True
    def disableMomentum(self):
        if 'Lenz' in self.decoderFamily():
            self.throttle.setF4(True)

    # On decoders that support disabling momentum, set the
    # appropriate function to False
    def enableMomentum(self):
        if 'Lenz' in self.decoderFamily():
            self.throttle.setF4(False)

    # Returns True if the loco has a block and the block
    # is a siding or reverse loop
    def isInSidings(self):
        if not self.block:
            return False
        if self.block.getUserName() in SOUTH_SIDINGS + NORTH_SIDINGS + [NORTH_REVERSE_LOOP, SOUTH_REVERSE_LOOP]:
            return True
        return False

    # Returns True if the loco has a block and that block
    # is visible
    def isVisible(self):
        if not self.block:
            return False
        return self.isBlockVisible(self.block)


