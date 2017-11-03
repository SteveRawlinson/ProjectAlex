import jmri
import time
from jmri_bindings import *
from myroutes import *

DEBUG = True

# status
SIDINGS = 1
MOVING = 2


class Loco:
    
    def __init__(self, dccAddr):
        self.dccAddr = dccAddr
        self._trainLength = None
        self._rosterEntry = None
        self._rarity = None
        self.roster = jmri.jmrit.roster.Roster.instance()
        self.block = None
        self.layoutBlock = None
        self.status = SIDINGS
        self._longAddr = None
        self._reversible = None
        self._highSpeed = None
        self._brclass = None
        self._passenger = None
        self._fast = None
        self.throttle = None
        self.wrongway = False

    def emergencyStop(self):
        self.throttle.setSpeedSetting(-1)

    def setSpeedSetting(self, speed):
        self.throttle.setSpeedSetting(speed)
        time.sleep(0.2)
        self.throttle.setSpeedSetting(speed)

    def forward(self):
        self.throttle.setIsForward(True)
        time.sleep(0.2)
        self.throttle.setIsForward(True)

    def reverse(self):
        self.throttle.setIsForward(False)
        time.sleep(0.2)
        self.throttle.setIsForward(False)


    def debug(self, message):
        if DEBUG:
            print "Loco: ", str(self.dccAddr) + ': ' + message

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
    def highSpeed(self):
        if self._highSpeed is None:
            r = self.rosterEntry().getAttribute('highspeed')
            if r is None:
                self._highSpeed = False  # this is the default
            if r == 'true':
                self._highSpeed = True
            else:
                self._highSpeed = False
        return self._highSpeed

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

    # Returns True if the block is longer than the current train.
    # The length of the train is determined by checking the 
    # attribute 'length' in the loco roster.
    def willFitInBlock(self, block):
        if block.getBlock().getLengthCm() > self.trainLength():
            self.debug("train will fit in block " + block.getId())
            return True
        self.debug("train won't fit in block " + block.getId() + ", block is " + str(block.getBlock().getLengthCm()) + " cms long, trains is " + str(self.trainLength()))
        return False

    # Takes an array of block names and returns the shortest empty block
    # that the current loco will fit in.
    def shortestBlockTrainFits(self, blocklist):
        start = time.time()
        sbtf = None
        while sbtf is None:
            for b in blocklist:
                block = layoutblocks.getLayoutBlock(b)
                mem = memories.getMemory("Siding " + b)
                if block is None:
                    self.debug("no such block: " + b)
                elif block.getState() == OCCUPIED:
                    pass
                    # self.debug("block " + b + " is occupied")
                elif mem is not None and mem.getValue() == "selected":
                    pass
                    # self.debug("block " + b + " is selected")

                elif mem is not None and mem.getValue() == "selected":
                    self.debug("block " + b + " is already selected")
                elif sbtf is None or block.getBlock().getLengthCm() < sbtf.getBlock().getLengthCm():
                    if self.willFitInBlock(block):
                        if DEBUG:
                            if sbtf is not None:
                                pass

                        sbtf = block
            if sbtf is None:
                self.debug("no available sidings")
                if time.time() - start > 60 * 5:
                    raise RuntimeError("timeout waiting for a free siding")
                time.sleep(10)
            else:
                self.debug("selected block " + sbtf.getId())
        return sbtf

    # Takes an array of block names and returns the shortest empty block
    # that the current loco will fit in. If no such blocks are available
    # it waits indefinitely.
    def shortestBlockTrainFitsBlocking(self, blocklist):
        sbtf = self.shortestBlockTrainFits(blocklist)
        while sbtf is None:
            time.sleep(5)
            sbtf = self.shortestBlockTrainFits(blocklist)
        return sbtf

    # Selects a siding from a list and sets a memory value to prevent
    # another loco selecting the same one.
    def selectSiding(self, sidings, blocking=True):
        if blocking:
            siding = self.shortestBlockTrainFitsBlocking(sidings)
        else:
            siding = self.shortestBlockTrainFits(sidings)
        mem = memories.provideMemory("IMSIDING" + siding.getId().upper())
        mem.setValue("selected")
        self.debug("selected siding " + siding.getId())
        return siding

    # Removes the memory which reserves the siding.
    def unselectSiding(self, siding):
        if  type(siding) == str:
            mem = memories.provideMemory("IMSIDING" + siding.upper())
        elif type(siding) == jmri.Block:
            mem = memories.provideMemory("IMSIDING" + siding.getUserName().upper())
        else:
            mem = memories.provideMemory("IMSIDING" + siding.getId().upper())
        mem.setValue(None)

    # Checks if the reverse loop (name) supplied is occupied
    # or already selected, returns None if so, or the block
    # if it's available
    def selectReverseLoop(self, loop):
        b = blocks.getBlock(loop)
        if b is None:
            raise RuntimeError("no such block: " + loop)
        if b.getState() == OCCUPIED:
            return None
        mem = memories.provideMemory("IMLOOP" + loop.upper())
        if mem.getValue() == "selected":
            return None
        mem.setValue("selected")
        return b

    def unselectReverseLoop(self, loop):
        mem = memories.provideMemory("IMLOOP" + loop.upper())
        mem.setValue(None)

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
        else:
            self.block = lblocks[0].getBlock()
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
        #self.debug("setting " + blk.getUserName() + " block to " + self.name())
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
