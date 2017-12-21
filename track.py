# A class to encapsulate a track route that goes
# north/south
import jmri
import time
from jmri_bindings import *
from myroutes import ROUTEMAP

DEBUG = True

class Track:

    def __init__(self, nr, stops, fast, unserviceable, blks, signal):
        self.nr = nr
        self.stops = stops
        self.fast = fast
        self.occupancy = 0
        self.us = unserviceable
        self.last_used = time.time()
        self.blocks = blks
        self.exitSignal = signals.getSignalHead(signal)

    def debug(self, message):
        if DEBUG:
            print "Track:", message

    # Selects a track from the list supplied for the loco supplied
    # according to the score for each track for that loco. Tracks
    # with equal high scores are sorted by the time they were last
    # used. If no tracks are available, returns None
    @classmethod
    def preferred_track(cls, loco, tracks):
        list = sorted(tracks, key=lambda t: t.score(loco, verbose=False), reverse=True)
        # if DEBUG:
        #     print "track in order of preference: "
        #     for t in list:
        #         print("track " + str(t.nr) + ": " + str(t.score(loco)) + " occupancy: " + str(t.occupancy))
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
        # if DEBUG:
        #     print "Track: returning selected track ", picked_s[0].nr, "score: ", picked_s[0].score(loco)
        return picked_s[0]

    # Returns a string describing the direction of travel for
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
    def score(self, loco, verbose=False):
        if verbose:
            print "getting score for track", self.nr
        if self.northbound() and loco.northSidings():
            return 0
        if self.southbound() and loco.southSidings():
            return 0
        if verbose:
            print "direction is fine"
        if self.busy():
            return 0
        if verbose:
            print "not busy"
        if self.us:
            return 0
        if verbose:
            print "not u/s"
        score = 0
        if self.fast:
            if loco.fast():
                score += 2
                if verbose:
                    print "fast status matched"
            elif loco.canGoFast():
                score += 1
                if verbose:
                    print "fast status semi-matched"
        else:
            if verbose:
                print "fast status not matched. self.fast:", self.fast, type(self.fast).__name__, "loco.fast():", loco.fast(), type(loco.fast()).__name__
        if self.fast is False and loco.freight():
            score += 1
            if verbose:
                print "freight loco on non-fast track match"
        if self.stops > 1 and loco.passenger():
            score += 2
            if verbose:
                print "passenger status matched"
        if verbose:
            print "returning score", str(score)
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
    # or North Slow/Fast Link if the supplied block is the northernmost
    # on this track.
    def nextBlockNorth(self, block):
        for b in self.blocks:
            if b == block.getUserName(): # this is the block we're in
                i = self.blocks.index(b) + 1
                if len(self.blocks) <= i:
                    if self.nr < 3:
                        nb = "North Slow Link"
                    else:
                        nb = 'North Fast Link'
                else:
                    nb = self.blocks[i]
                return blocks.getBlock(nb)
        # the block supplied is not on this track
        self.debug("block " + block.getUserName() + " is not part of track " + str(self.nr))
        return None

    # See comment for nextBlockNorth() above
    def nextBlockSouth(self, block):
        myblocks = self.blocks[:]
        myblocks.reverse()
        for b in myblocks:
            #self.debug("nBS: checking block " + b)
            if b == block.getUserName():  # this is the block we're in
                i = myblocks.index(b) + 1
                #self.debug("  index is " + str(i))
                if len(myblocks) <= i:
                    nb = 'South Link'
                else:
                    nb = myblocks[i]
                    #self.debug("  returning block " + nb)
                return blocks.getBlock(nb)
        # the block supplied is not on this track
        self.debug("block " + block.getUserName() + " is not part of track " + str(self.nr))
        return None

    def northernmostBlock(self):
        return self.blocks[-1]

    def southernmostBlock(self):
        return self.blocks[0]

    def lastBlock(self):
        if self.northbound():
            return self.northernmostBlock()
        else:
            return self.southernmostBlock()


    # returns the name of the route to set for exiting this track to sidings
    def exitRoute(self, reverse = False):
        if (self.northbound() and reverse is False) or (self.southbound() and reverse is True):
            farBlock = self.northernmostBlock()
        else:
            farBlock = self.southernmostBlock()
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

    # Returns a count of the southbound tracks not in use
    @classmethod
    def southboundTracksFree(cls, tracks):
        count = 0
        for t in tracks:
            if t.southbound() and t.busy() is False:
                count += 1
        return count

    # Returns a count of the southbound tracks not in use
    @classmethod
    def northboundTracksFree(cls, tracks):
        count = 0
        for t in tracks:
            if t.northbound() and t.busy() is False:
                count += 1
        return count

    @classmethod
    def trackReport(self, tracks):
        for t in tracks:
            print "track nr:", t.nr, "occupancy:", t.occupancy, "u/s:", t.us, "northBound:", t.northbound()

    # sets the exit signal for this track to the colour specified
    def setExitSignalAppearance(self, appearance):
        if self.exitSignal is None:
            return
        if self.exitSignal.getAppearance == appearance:
            return
        self.exitSignal.setAppearance(appearance)
