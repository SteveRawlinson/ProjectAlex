import jmri
import time
from jmri_bindings import layoutblocks
from jmri_bindings import blocks
from jmri_bindings import OCCUPIED

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
        self.status = SIDINGS


    def debug(self, message):
        if DEBUG:
            print "Loco:", message

    # Returns the roster ID (ie. the name)
    def name(self):
        return self.rosterEntry().getId()

    # Returns the length of the train, as recorded in the attribute
    # 'length' in the loco roster.
    def trainLength(self):
        if self._trainLength is None:
            self._trainLength = float(self.rosterEntry().getAttribute('length'))
        return float(self._trainLength)

    def rarity(self):
        if self._rarity is None:
            r = self.rosterEntry().getAttribute('rarity')
            if type(r) == str:
                self._rarity = float(r)
            else:
                self._rarity = 0
        return self._rarity
    
    # Returns the roster entry for the current loco
    def rosterEntry(self):
        if self._rosterEntry is None:
            self.debug("getting roster entry for " + str(self.dccAddr))
            roster_entries = self.roster.getEntriesByDccAddress(str(self.dccAddr))
            if len(roster_entries) == 0:
                raise RuntimeError("no Roster Entry for address", str(self.dccAddr))
            self._rosterEntry = roster_entries[0]

        return self._rosterEntry

    # Returns True if the block is longer than the current train.
    # The length of the train is determined by checking the 
    # attribute 'length' in the loco roster.
    def willFitInBlock(self, block):
        if block.getBlock().getLengthCm() > self.trainLength():
            print "train will fit"
            return True
        print "train won't fit, block is ", block.getBlock().getLengthCm(), "cms long, trains is", self.trainLength()
        return False

    # Takes an array of block names and returns the shortest empty block
    # that the current loco will fit in.
    def shortestBlockTrainFits(self, blocklist):
        sbtf = None
        print "looking for shortest block that will fit loco", self.dccAddr, "which is", self.trainLength, "cms"
        for b in blocklist:
            self.debug("considering block " + b)
            block = layoutblocks.getLayoutBlock(b)
            if block is None:
                self.debug("no such block: " + b)
            elif block.getState() == OCCUPIED:
                self.debug("block " + b + " is occupied")
            elif sbtf is None or block.getBlock().getLengthCm() < sbtf.getBlock().getLengthCm():
                self.debug("might assign block to sbtf")
                if self.willFitInBlock(block):
                    self.debug("assigning")
                    sbtf = block
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

    # Returns the the layout block(s) I'm in
    def myLayoutBlocks(self):
        #return layoutblocks.getLayoutBlocksOccupiedByRosterEntry(self.rosterEntry())
        blockList = []
        for name in blocks.getSystemNameList():
            lob = layoutblocks.getLayoutBlock(name)
            if lob is not None:
                b = lob.getBlock()
                if type(b.getValue()) == jmri.jmrit.roster.RosterEntry and b.getValue() == self.rosterEntry():
                    blockList.append(lob)
                elif b.getValue() == self.rosterEntry().getId() or b.getValue() == self.dccAddress:
                    blockList.append(lob)
        return blockList

    # Sets the instance variable 'block' using information
    # from the layout
    def initBlock(self):
        lblocks = self.myLayoutBlocks()
        if len(lblocks) == 0:
            self.block = None
        elif len(lblocks) > 1:
            self.block = "multi"
        else:
            self.block = lblocks[0]
        return self.block

    # Sets this loco's block to b (if it's a block)
    # or to b's block (if it's a layoutblock) or to
    # the block whose name is b (it it's a string).
    # Also sets the block's value to the loco's
    # dcc address.
    def setBlock(self, b):
        self.debug("type: " + type(b).__name__)
        if type(b) == str or type(b) == unicode:
            self.debug("string")
            lblk = layoutblocks.getLayoutBlock(b)
            blk = lblk.getBlock()
        elif type(b) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            self.debug("layoutblock")
            blk = b.getBlock()
        else:
            self.debug("block")
            blk = b
        self.debug("setting " + blk.getUserName() + " block to " + self.name())
        self.block = blk
        blk.setValue(str(self.dccAddr))
        self.debug("new block value: " + blk.getValue())
