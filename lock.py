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
        self.northFastLink = False
        self.northSlowLink = False
        self.northSidings = False
        # values read from the memories
        self.southSidingsVal = None
        self.southTrackLinkVal = None
        self.northFastLinkVal = None
        self.northSlowLinkVal = None
        self.northSidingsVal = None


    # Read the appropriate memory values indicating whether bits of track
    # are locked by other locos and fill in some variables
    def readMemories(self, end, addr):
        if end == SOUTH:
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
            self.northFastLinkVal = m.getValue()
            if self.northFastLinkVal == "" or self.northFastLinkVal == addr:
                self.northFastLinkVal = None
            m = memories.provideMemory("IMLOCKNORTHSLOWLINK")
            self.northSlowLinkVal = m.getValue()
            if self.northSlowLinkVal == "" or self.northSlowLinkVal == addr:
                self.northSlowLinkVal = None
            m = memories.provideMemory("IMLOCKNORTHSIDINGS")
            self.northSidingsVal = m.getValue()
            if self.northSidingsVal == "" or self.northSidingsVal == addr:
                self.northSidingsVal = None

    # Write our loco's dcc address into the values of memories we have
    # got a lock on
    def writeMemories(self):
        if self.end == SOUTH:
            if self.southSidings:
                m = memories.provideMemory("IMLOCKSOUTHSIDINGS")
                m.setValue(self.loco.dccAddr)
            if self.southTrackLink:
                m = memories.provideMemory("IMLOCKSOUTHTRACKLINK")
                m.setValue(self.loco.dccAddr)
        else:
            if self.northFastLink:
                m = memories.provideMemory("IMLOCKNORTHFASTLINK")
                m.setValue(self.loco.dccAddr)
            if self.northSlowLink:
                m = memories.provideMemory("IMLOCKNORTHSLOWLINK")
                m.setValue(self.loco.dccAddr)
            if self.northSidings:
                m = memories.provideMemory("IMLOCKNORTHSIDINGS")
                m.setValue(self.loco.dccAddr)

    def empty(self):
        if self.northSidings or self.northSlowLink or self.northFastLink or self.southTrackLink or self.southSidings:
            return False
        return True

    # attempt to get a lock
    def getLockNonBlocking(self, end, direction, trak, loc):
        self.end = end
        self.direction = direction
        self.loco = loc
        self.readMemories(str(loc.dccAddr))
        if end == NORTH:
            # North Link, Northbound
            if direction == NORTHBOUND:
                if trak.nr > 2:
                    if self.northFastLinkVal is None:
                        self.northFastLink = True
                else:
                    if self.northSlowLinkVal is None:
                        self.northSlowLink = True
                if self.northSidingsVal is None:
                    self.northSidings = True
            else:
                # North Link, Southbound
                if self.northSidingsVal or self.northFastLinkVal or self.northSlowLinkVal:
                    # no lock available
                    pass
                else:
                    # everything is available
            self.northSlowLink = self.northFastLink = self.northSidings = True
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
        self.writeMemories(end, loc)

    def getLock(self, end, direction, trak, loc):
        while self.empty():
            self.getLockNonBlocking(end, direction, trak, loc)
            if self.empty():
                time.sleep(1)

    def unlock(self):
        self.readmemories(self.end)
