# A class to encapsulate a track route that goes
# north/south
import time

class Track:

    def __init__(self, nr, stops, fast):
        self.nr = nr
        self.stops = stops
        self.fast = fast
        self.occupancy = 0
        self.last_used = time.time()

    # Selects a track from the list supplied for the loco supplied
    # according to the score for each track for that loco. Tracks
    # with equal high scores are sorted by the time they were last
    # used.
    @classmethod
    def preferred_track(cls, loco, tracks):
        list = sorted(tracks, key=lambda t: t.score, reverse=True)
        if len(list) == 0:
            return None
        picked = []
        for t in list:
            if t.score(loco) == list[0].score(loco)
            picked.append(t)
        picked_s = sorted(picked, key=lambda t: t.last_used)
        return picked_s[0]



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
        if self.northbound() and loco.southSidings():
            return 0
        if self.southbound() and loco.northSidings():
            return 0
        if self.busy:
            return 0
        score = 0
        if self.fast and loco.fast:
            score += 1
        if self.stops > 1 and loco.passenger:
            score += 1
        return score


