from myroutes import *
from jmri_bindings import *
import loco
import track
import util

class Lock(util.Util):

    def __init__(self):
        self.direction = None
        self.end = None
        self.loco = None
        # values to indicate the areas we have locked
        self.southSidings = False
        self.southTrackLink = False
        self.northTrackLink = False
        self.northSidings = False
        # values read from the memories
        self.southSidingsVal = None
        self.southTrackLinkVal = None
        self.northTrackLinkVal = None
        self.northSidingsVal = None


    # Read the appropriate memory values indicating whether bits of track
    # are locked by other locos and fill in some variables
    def readMemories(self):
        addr = str(self.loco.dccAddr)
        if self.end == SOUTH:
            m = memories.provideMemory("IMLOCKSOUTHSIDINGS")
            self.southSidingsVal = m.getValue()
            if self.southSidingsVal == "" or self.southSidingsVal == addr:
                self.southSidingsVal = None
            m = memories.provideMemory("IMLOCKSOUTHTRACKLINK")
            self.southTrackLinkVal = m.getValue()
            if self.southTrackLinkVal == "" or self.southTrackLinkVal == addr:
                self.southTrackLinkVal = None
        else:
            m = memories.provideMemory("IMLOCKNORTHFASTLINK")
            self.northTrackLinkVal = m.getValue()
            if self.northTrackLinkVal == "" or self.northTrackLinkVal == addr:
                self.northTrackLinkVal = None
            m = memories.provideMemory("IMLOCKNORTHSIDINGS")
            self.northSidingsVal = m.getValue()
            if self.northSidingsVal == "" or self.northSidingsVal == addr:
                self.northSidingsVal = None

    # Write our loco's dcc address into the values of memories we have
    # got a lock on and None into values of memories we haven't, if and
    # only if we had those locks at the time of calling
    def writeMemories(self):
        if self.end == SOUTH:
            m = memories.provideMemory("IMLOCKSOUTHSIDINGS")
            if self.southSidings:
                m.setValue(self.loco.dccAddr)
            elif self.southSidingsVal == str(self.loco.dccAddr):
                m.setValue(None)
            m = memories.provideMemory("IMLOCKSOUTHTRACKLINK")
            if self.southTrackLink:
                m.setValue(self.loco.dccAddr)
            elif self.southTrackLinkVal == str(self.loco.dccAddr):
                m.setValue(None)
        else:
            m = memories.provideMemory("IMLOCKNORTHTRACKLINK")
            if self.northTrackLink:
                m.setValue(self.loco.dccAddr)
            elif self.northTrackLinkVal == str(self.loco.dccAddr):
                m.setValue(None)
            m = memories.provideMemory("IMLOCKNORTHSIDINGS")
            if self.northSidings:
                m.setValue(self.loco.dccAddr)
            elif self.northSidingsVal == str(self.loco.dccAddr):
                m.setValue(None)

    # Returns true if we haven't locked anything (False otherwise)
    def empty(self):
        if self.northSidings or self.northTrackLink or self.southTrackLink or self.southSidings:
            return False
        return True

    # Attempt to get a lock or partial lock.
    #
    # Each end of the layout (NORTH end and SOUTH end) has a link
    # between the tracks on the layout and the (hidden) sidings at that
    # end. Each link is split into two parts - the track link part
    # and the sidings part. A loco approaching a link can call for a
    # lock and will be granted a one on both parts of the link if it's
    # free, or, possibly a partial lock on the half part of the link
    # closest to it if the other part is locked by another loco moving
    # in the same direction.
    #
    # A loco given a full lock can release the part behind it as it moves
    # through the link, allowing a following loco to get a partial
    # lock on that part and move into the link.
    #
    # A loco which gets a partial lock must wait in the middle until
    # a full lock is available.
    #
    # This method returns immediately even if no lock is available.
    def getLockNonBlocking(self, end, direction, loc):
        self.end = end
        self.direction = direction
        self.loco = loc
        self.readMemories()
        if end == NORTH:
            # North Link, Northbound
            if direction == NORTHBOUND:
                if self.northTrackLinkVal is None:
                    self.northTrackLink = True
                if self.northSidingsVal is None:
                    self.northSidings = True
            else:
                # North Link, Southbound
                if self.northSidingsVal or self.northFastLinkVal or self.northSlowLinkVal:
                    # no lock available
                    pass
                else:
                    # everything is available
                    self.northTrackLink = self.northSidings = True
        else: # end == SOUTH
            # South Link, Southbound
            if direction == SOUTHBOUND:
                if self.southTrackLinkVal is None:
                    self.southTrackLink = True
                if self.southSidingsVal is None:
                    self.southSidings = True
            else:
                # South Link, Northbound
                if self.southSidingsVal or self.southTrackLinkVal:
                    pass
                else:
                    self.southTrackLink = self.southSidings = True
        self.writeMemories()

    # Calls the above method repeatedly until at least a partial lock
    # is available.
    def getLock(self, end, direction, loc):
        while self.empty():
            self.getLockNonBlocking(end, direction, loc)
            if self.empty():
                time.sleep(1)


    # Upgrades a lock from a partial to a full lock then
    # unlocks the other part.
    def upgradeLock(self):
        while True:
            self.readMemories()
            if self.end == NORTH:
                if self.direction == NORTHBOUND:
                    if self.northSidingsVal is None:
                        self.northSidings = True
                        self.northTrackLink = None
                        break
                else:
                    if self.northTrackLinkVal is None:
                        self.northTrackLink = True
                        self.northSidings = None
                        break
            else:
                if self.direction == SOUTHBOUND:
                    if self.southSidingsVal is None:
                        self.southSidings = True
                        self.southTrackLink = None
                        break
                else:
                    if self.southTrackLinkVal is None:
                        self.southTrackLink = True
                        self.southSidings = None
                        break
            time.sleep(0.5)
        self.writeMemories()


    def status(self):
        str = "Lock status: "
        str += str(self.loco.dccAddr) + ' '
        str += "end: "
        if self.end == NORTH:
            str += "North "
        else:
            str += "South "
        str += "dir: "
        if self.direction == SOUTHBOUND:
            str += "Southbound "
        else:
            str += "Northbound "
        if self.empty():
            str += " EMPTY"
        else:
            str += " sidings: "
            if self.northSidings or self.southSidings:
                str += " LOCKED "
            else:
                str += " unlocked "
            str += " Tracklink: "
            if self.northTrackLink or self.southTrackLink:
                str += " LOCKED"
            else:
                str += " unlocked"



    # Releases all or part of a lock.
    def unlock(self, partial=False):
        self.readmemories(self.end)
        if self.end == NORTH:
            if self.northSidings:
                if self.northSidingsVal != str(self.loco.dccAddr):
                    raise RuntimeError(
                        "loco" + self.loco.nameAndAddress() + " attempted to remove a lock on northSidings it does not own")
                elif partial is False:
                    self.northSidings = None
                elif partial is True and self.direction == SOUTHBOUND:
                    self.northSidings = None
            if self.northTrackLink:
                if self.northTrackLinkVal != str(self.loco.dccAddr):
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on northTrackLink it does not own")
                elif partial is False:
                    self.northTrackLink = None
                elif partial is True and self.direction == NORTHBOUND:
                    self.northTrackLink = None
        else:
            if self.southSidings:
                if self.southSidingsVal != str(self.loco.dccAddr):
                    raise RuntimeError(
                        "loco" + self.loco.nameAndAddress() + " attempted to remove a lock on southSidings it does not own")
                elif partial is False:
                    self.southSidings = None
                elif partial is True and self.direction == NORTHBOUND:
                    self.southSidings = None
            if self.southTrackLink:
                if self.southTrackLinkVal != str(self.loco.dccAddr):
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on southTracklink it does not own")
                elif partial is False:
                    self.southTrackLink = None
                elif partial is True and self.direction == SOUTHBOUND:
                    self.southTrackLink = None
        self.writeMemories()

    # Releases part of a lock
    def partialUnlock(self):
        self.unlock(partial=True)




