# A class to encapsulate a track route that goes
# north/south
import jmri
import time
from jmri_bindings import *
from myroutes import ROUTEMAP

DEBUG = True

class Track:

    def __init__(self, nr, stops, fast, unserviceable, blks):
        self.nr = nr
        self.stops = stops
        self.fast = fast
        self.occupancy = 0
        self.us = unserviceable
        self.last_used = time.time()
        self.blocks = blks

    def debug(self, message):
        if DEBUG:
            print "Track:", message

    # Selects a track from the list supplied for the loco supplied
    # according to the score for each track for that loco. Tracks
    # with equal high scores are sorted by the time they were last
    # used. If no tracks are available, returns None
    @classmethod
    def preferred_track(cls, loco, tracks):
        list = sorted(tracks, key=lambda t: t.score(loco), reverse=True)
        # if DEBUG:
        #     print "track in order of preference: "
        #     for t in list:
        #         print("track " + str(t.nr) + ": " + str(t.score(loco)))
        if len(list) == 0:
            return None
        if list[0].score(loco) == 0:
            return None
        picked = []
        for t in list:
            if t.score(loco) == list[0].score(loco):
                picked.append(t)
        #if DEBUG:
        #    print(str(len(picked)) + " tracks picked")
        picked_s = sorted(picked, key=lambda t: t.last_used)
        if picked_s[0].score(loco) == 0:
            return None
        if DEBUG:
            print "Track: returning selected track ", picked_s[0].nr, "score: ", picked_s[0].score(loco)
        return picked_s[0]

    # Returns a string descriving the direction of travel for
    # this track
    def dir(self):
        if self.northbound():
            return 'Sth2Nth'
        return 'Nth2Sth'

    # Returns true if normal traffic on this track goes north
    def northbound(self):
        return self.nr % 2 == 0

    # Returns true if normal traffic on this track goes south
    def southbound(self):
        return not self.northbound()

    # Returns true if there are any trains on me
    def busy(self):
        return self.occupancy > 0

    # Returns a number which is an indication of the suitability
    # of this track for this locomotive. Zero means it can't be
    # used, higher scores indicate more suitability
    def score(self, loco):
        if self.northbound() and loco.northSidings():
            return 0
        if self.southbound() and loco.southSidings():
            return 0
        if self.busy():
            return 0
        if self.us:
            return 0
        score = 0
        if self.fast and loco.fast():
            score += 1
        if self.stops > 1 and loco.passenger:
            score += 1
        return score

    # Returns the track object in the list of tracks
    # supplied that contains the block supplied. The
    # block can be a string, a block, or a layoutBlock
    @classmethod
    def findTrackByBlock(cls, tracks, block):
        print "findTrackByBlock: block type is: " + type(block).__name__
        blockName = None
        if type(block) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            blockName = block.getBlock().getUserName()
        elif type(block) == jmri.Block:
            blockName = block.getUserName()
        if blockName is None:
            raise RuntimeError("Can't find block name")
        for t in tracks:
            if blockName in t.blocks:
                return t
        return None

    # Returns the next monitored block on this track northbound
    # from the block supplied (which must be a jmri.Block),
    # or North Link if the supplied block is the northernmost
    # on this track.
    def nextBlockNorth(self, block):
        for b in self.blocks:
            if b == block.getUserName(): # this is the block we're in
                i = self.blocks.index(b) + 1
                if len(self.blocks) <= i:
                    nb = 'South Link'
                else:
                    nb = self.blocks[i]
                return blocks.getBlock(nb)
        # the block supplied is on on this track
        self.debug("block " + block.getUserName() + " is not part of track " + str(self.nr))
        return None

    # See comment for nextBlockNorth() above
    def nextBlockSouth(self, block):
        myblocks = self.blocks[:]
        myblocks.reverse()
        for b in myblocks:
            if b == block.getUserName():  # this is the block we're in
                i = myblocks.index(b) + 1
                if len(myblocks) <= i:
                    nb = 'South Link'
                else:
                    nb = self.blocks[i]
                return blocks.getBlock(nb)
        # the block supplied is on on this track
        self.debug("block " + block.getUserName() + " is not part of track " + str(self.nr))
        return None

    def northernmostBlock(self):
        return self.blocks[-1]

    def southernmostBlock(self):
        return self.blocks[0]

    # returns the name of the route to set for exiting this track to sidings
    def exitRoute(self, reverse = False):
        if (self.northbound() and reverse is False) or (self.southbound() and reverse is True):
            farBlock = self.northernmostBlock()
        else:
            farBlock = self.southernmostBlock()
        self.debug("farblock: " + farBlock)
        routes = ROUTEMAP[farBlock]
        return routes[0] # there's only one

    # returns the name of the route to set for entering this track from the sidings
    def entryRoute(self, reverse = False):
        if (self.northbound() and reverse is False) or (self.southbound() and reverse is True):
            farBlock = self.southernmostBlock()
        else:
            farBlock = self.northernmostBlock()
        routes = ROUTEMAP[farBlock]
        return routes[0] # only one





