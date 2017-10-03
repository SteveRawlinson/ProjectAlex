# A class to encapsulate a track route that goes
# north/south
import time

DEBUG = True

class Track:

    def __init__(self, nr, stops, fast, unserviceable, blocks):
        self.nr = nr
        self.stops = stops
        self.fast = fast
        self.occupancy = 0
        self.us = unserviceable
        self.last_used = time.time()
        self.blocks = blocks

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
        if type(block) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            block = block.getBlock().getId()
        elif type(block) == jmri.Block:
            block = block.getId()
        for t in tracks:
            if block in t.blocks:
                return t
        return None



