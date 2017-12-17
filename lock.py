import jmri
from myroutes import *
from jmri_bindings import *
import loco
import track
import util
import time
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
        addr = self.loco.dccAddr
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
            m = memories.provideMemory("IMLOCKNORTHTRACKLINK")
            self.northTrackLinkVal = m.getValue()
            if self.northTrackLinkVal == "" or self.northTrackLinkVal == addr:
                self.northTrackLinkVal = None
            m = memories.provideMemory("IMLOCKNORTHSIDINGS")
            self.northSidingsVal = m.getValue()
            if self.northSidingsVal == "" or self.northSidingsVal == addr:
                self.northSidingsVal = None
        self.log("readMemories: ")
        self.log("  southSidingsVal: "+ str(self.southSidingsVal))
        self.log("  southTrackLinkVal: " + str(self.southTrackLinkVal))
        self.log("  northSidingsVal: " + str(self.northSidingsVal))
        self.log("  northTrackLinkVal: " + str(self.northTrackLinkVal))

    # Write our loco's dcc address into the values of memories we have
    # got a lock on and None into values of memories we haven't, if and
    # only if we had those locks at the time of calling.
    def writeMemories(self):
        self.log("writeMemories: ")
        self.log("  southSidings: " + str(self.southSidings))
        self.log("  southTrackLink: " + str(self.southTrackLink))
        self.log("  northSidings: " + str(self.northSidings))
        self.log("  northTrackLink: " + str(self.northTrackLink))
        self.log(self.status())
        if self.end == SOUTH:
            m = memories.provideMemory("IMLOCKSOUTHSIDINGS")
            if self.southSidings:
                if self.southSidings is True:
                    m.setValue(self.loco.dccAddr)
                else:
                    m.setValue(self.southSidings)
            elif self.southSidingsVal is None:
                m.setValue(None)
            else:
                # must be false or zero (which is in fact false), leave it alone
                pass
            m = memories.provideMemory("IMLOCKSOUTHTRACKLINK")
            if self.southTrackLink:
                if self.southTrackLink is True:
                    m.setValue(self.loco.dccAddr)
                else:
                    m.setValue(self.southTrackLink)
            elif self.southTrackLinkVal is None:
                m.setValue(None)
        else: # NORTH
            m = memories.provideMemory("IMLOCKNORTHTRACKLINK")
            if self.northTrackLink:
                if self.northTrackLink is True:
                    m.setValue(self.loco.dccAddr)
                else:
                    m.setValue(self.northTrackLink)
            elif self.northTrackLinkVal is None:
                m.setValue(None)
            m = memories.provideMemory("IMLOCKNORTHSIDINGS")
            if self.northSidings:
                if self.northSidings is True:
                    m.setValue(self.loco.dccAddr)
                else:
                    m.setValue(self.northSidings)
            elif self.northSidingsVal is None:
                m.setValue(None)

    # Returns true if we haven't locked anything (False otherwise)
    def empty(self):
        if self.northSidings is True or self.northTrackLink is True or self.southTrackLink is True or self.southSidings is True:
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
    def getLockNonBlocking(self, end=None, direction=None, loc=None):
        if end is not None:
            self.end = end
        if direction is not None:
            self.direction = direction
        if loc is not None:
            self.loco = loc
        if self.end is None or self.direction is None or self.loco is None:
            self.debug("end: " + str(self.end))
            self.debug("direction: " + str(self.direction))
            if self.loco:
                self.debug("loc: " + str(self.loco.dccAddr))
            raise RuntimeError("must specify end, direction and loco")
        if powermanager.getPower() == jmri.PowerManager.OFF:
            self.debug('power is off, not getting lock')
            return
        self.readMemories()
        if DEBUG:
            if end == NORTH:
                end_s = 'North'
            else:
                end_s = 'South'
            if direction == SOUTHBOUND:
                dir_s = 'Southbound'
            else:
                dir_s = 'Northbound'
            self.log("attempting lock on " + end_s + " Link direction " + dir_s)
        if end == NORTH:
            # North Link, Northbound (leaving the layout)
            if direction == NORTHBOUND:
                if self.northTrackLinkVal is None:
                    self.northTrackLink = True
                    if self.northSidingsVal is None:
                        self.northSidings = True
            else:
                # North Link, Southbound (coming out to sidings)
                if self.northSidingsVal or self.northTrackLinkVal:
                    # no lock available
                    pass
                else:
                    # everything is available
                    self.northTrackLink = self.northSidings = True
        else: # end == SOUTH
            # South Link, Southbound (leaving the layout)
            if direction == SOUTHBOUND:
                if self.southTrackLinkVal is None:
                    self.southTrackLink = True
                    if self.southSidingsVal is None:
                        self.southSidings = True
            else:
                # South Link, Northbound (coming out of sidings)
                if self.southSidingsVal is None:
                    self.southSidings = True
                    if self.southTrackLinkVal is None:
                        self.southTrackLink = True
                # if self.southSidingsVal or self.southTrackLinkVal:
                #     pass
                # else:
                #     self.southTrackLink = self.southSidings = True
        # set the signal if we're leaving the layout
        if (end == NORTH and direction == NORTHBOUND) or (end == SOUTH and direction == SOUTHBOUND):
            signal = self.loco.track.exitSignal
            if signal is not None:
                if self.empty():
                    if signal.getAppearance != RED:
                        signal.setAppearance(RED)
                else:
                    if signal.getAppearance != GREEN:
                        signal.setAppearance(GREEN)
        self.writeMemories()
        self.log(self.status())

    # Calls the above method repeatedly until at least a partial lock
    # is available.
    def getLock(self, end=None, direction=None, loc=None):
        if DEBUG:
            if end == NORTH or self.end == NORTH:
                end_s = 'North'
            else:
                end_s = 'South'
            self.debug(str(loc.dccAddr) + " getting (blocking) lock on " + end_s + " link")
        while self.empty():
            self.getLockNonBlocking(end, direction, loc)
            if self.empty():
                time.sleep(0.5)

    # Get a lock on the whole link, emulating the old style lock
    def getOldLockNonBlocking(self, end, direction, loc):
        self.end = end
        self.direction = direction
        self.loco = loc
        self.readMemories()
        if end == NORTH:
            if self.northSidingsVal or self.northTrackLinkVal:
                # no lock available
                pass
            else:
                # everything is available
                self.northTrackLink = self.northSidings = True
        else:
            if self.southSidingsVal or self.southTrackLinkVal:
                pass
            else:
                self.southTrackLink = self.southSidings = True
        self.writeMemories()

    def getOldLock(self, end, direction, loc):
        while self.empty():
            self.getOldLockNonBlocking(end, direction, loc)
            if self.empty():
                time.sleep(0.5)


    def upgradeLockNonBlocking(self, keepOldPartial=False):
        if powermanager.getPower() == jmri.PowerManager.OFF:
            self.debug('power is off, not upgrading lock')
        self.readMemories()
        if self.end == NORTH:
            if self.direction == NORTHBOUND:
                if self.northSidingsVal is None:
                    self.northSidings = True
                    if not keepOldPartial:
                        self.northTrackLink = None
                    return True
            else:
                if self.northTrackLinkVal is None:
                    self.northTrackLink = True
                    if not keepOldPartial:
                        self.northSidings = None
                    return True
        else:
            if self.direction == SOUTHBOUND:
                if self.southSidingsVal is None:
                    self.southSidings = True
                    if not keepOldPartial:
                        self.southTrackLink = None
                    return True
            else:
                if self.southTrackLinkVal is None:
                    self.southTrackLink = True
                    if not keepOldPartial:
                        self.southSidings = None
                    return True
        return False

    # Upgrades a lock from a partial to a full lock then
    # unlocks the other part (unless keepOldPartial is True)
    def upgradeLock(self, keepOldPartial=False):
        while self.upgradeLockNonBlocking(keepOldPartial) is False:
            time.sleep(0.5)
        self.writeMemories()


    # Return a string describing this lock
    def status(self):
        s = "Lock status: "
        s += str(self.loco.dccAddr) + ' '
        s += "end: "
        if self.end == NORTH:
            s += "North "
        else:
            s += "South "
        s += "dir: "
        if self.direction == SOUTHBOUND:
            s += "Southbound "
        else:
            s += "Northbound "
        if self.empty():
            s += " EMPTY"
        else: # not empty
            s += " sidings: "
            if self.northSidings or self.southSidings:
                s += " LOCKED "
            else:
                s += " unlocked "
            s += " Tracklink: "
            if self.northTrackLink or self.southTrackLink:
                s += " LOCKED"
            else:
                s += " unlocked"
        return s



    # Releases all or part of a lock. This is considerably more complicated than
    # you might imagine.
    def unlock(self, partialUnlock=False):
        # make a note of whether this was a partial lock before we start unlocking bits
        self.readMemories()
        if self.end == NORTH:
            # North Link
            if self.northSidings:
                # check we actually hold the lock
                if self.northSidingsVal is not None and self.northSidingsVal != self.loco.dccAddr:
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on northSidings it does not own")
                elif partialUnlock is False:
                    self.northSidings = None
                    if self.direction == NORTHBOUND:
                        if self.northTrackLinkVal is not None:
                            # see long comment down there vv
                            self.northSidings = self.northTrackLinkVal
                elif partialUnlock is True and self.direction == SOUTHBOUND:
                    self.northSidings = None
            if self.northTrackLink:
                if self.northTrackLinkVal is not None and self.northTrackLinkVal != self.loco.dccAddr:
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on northTrackLink it does not own")
                elif partialUnlock is False:
                    self.northTrackLink = None
                    if self.direction == SOUTHBOUND:
                        if self.northSidingsVal is not None:
                            # see long comment down there
                            self.northTrackLink = self.northSidingsVal
                elif partialUnlock is True and self.direction == NORTHBOUND:
                    self.northTrackLink = None
        else:
            # South Link
            if self.southSidings:
                # check we actually hold the lock
                if self.southSidingsVal is not None and self.southSidingsVal != self.loco.dccAddr:
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on southSidings it does not own")
                elif partialUnlock is False:
                    # partial == False, set everything to None
                    self.southSidings = None
                    if self.direction == SOUTHBOUND:
                        # southSidings is the last part of the lock and we've just released it
                        if self.southTrackLinkVal is not None:
                            # another loco has the other end of the lock and it must also be moving south.
                            # Make sure it gets this part now otherwise a northbound loco might get a partial
                            # lock and we get a deadlock: two partial locks held by locos moving in different
                            # directions. Neither can move.
                            self.southSidings = self.southTrackLinkVal
                elif partialUnlock is True and self.direction == NORTHBOUND:
                    # we are doing a partial unlock but we can release the sidings part anyway because we're heading out to the layout
                    self.southSidings = None
            if self.southTrackLink:
                # check we hold the lock
                if self.southTrackLinkVal is not None and self.southTrackLinkVal != self.loco.dccAddr:
                    raise RuntimeError("loco" + self.loco.nameAndAddress() + " attempted to remove a lock on southTracklink it does not own")
                elif partialUnlock is False:
                    # full unlock - set everything to None
                    self.southTrackLink = None
                    if self.direction == NORTHBOUND:
                        if self.southSidingsVal is not None:
                            # see long comment up there ^
                            self.southTrackLink = self.southSidingsVal
                elif partialUnlock is True and self.direction == SOUTHBOUND:
                    # we are doing a partial unlock and this is the bit that needs to be unlocked
                    self.southTrackLink = None
        self.debug(self.status())
        self.writeMemories()

    # Releases part of a lock
    def partialUnlock(self):
        self.unlock(partialUnlock=True)

    # Returns true if this lock has part of a link locked
    def partial(self):
        if self.end == NORTH:
            return self.northSidings is not self.northTrackLink
        else:
            return self.southSidings is not self.southTrackLink

    # The method is called when the loco reaches the halfway point covered
    # by the lock. It needs either to upgrade to a full lock in order
    # to progress (in the case of it having a partial lock), or it needs
    # to release the first part of the lock (in the case of having a full
    # lock).
    def switch(self):
        if self.empty():
            self.debug("****************************** switch called on empty lock ^^^^^^^^^^^^^^^^^^^^^^")
            return
        if self.partial():
            self.debug("upgrading partial lock")
            self.log("upgrading partial lock")
            if self.loco.throttle.getSpeedSetting() > 0:
                # this is a convoluted way of slowing and then stopping the loco while we
                # upgrade the lock to a full lock
                if self.upgradeLockNonBlocking() is False:
                    self.debug("slowing loco while lock upgraded")
                    self.loco.setSpeedSetting('slow')
                    tries = 0
                    while self.upgradeLockNonBlocking() is False and tries < 5:
                        time.sleep(0.5)
                        tries += 1
                    if not self.partial():
                        return
                    self.debug("stopping loco until lock upgraded")
                    self.loco.setSpeedSetting(0)
                    tries = 0
                    while self.upgradeLockNonBlocking() is False and tries < 5:
                        time.sleep(0.5)
                        tries += 1
                    if not self.partial():
                        return
                    self.loco.emergencyStop()
                    self.upgradeLock()
            self.upgradeLock()
        else:
            self.debug("partial unlock")
            self.partialUnlock()

    # slows a loco down to 'slow' speed and then tries to get the lock
    # as it's going slowly until slowtime expires. If it gets the lock
    # it returns, if the time expires it stops the loco and and then
    # waits till the lock is got.
    def getLockOrStopLoco(self, destination):
        self.loco.setSpeedSetting('slow')
        slowtime = self.getSlowtime(destination)
        tn = time.time()
        while self.empty() and ((time.time() - tn) < slowtime):
            sleep(0.25)
            self.getLockNonBlocking()
        if self.empty():
            self.loco.setSpeedSetting(0)
        else:
            return
        # wait for a lock
        self.getLock()

    # Undoes this lock after checkLock() discovers a discrepancy
    # between the lock and the actual memory values held by JMRI.
    # This can happen as a result of a race condition. Setting the
    # values to None gets the corresponding memory value set to
    # None whereas setting them to False leaves the value alone
    # when we call writeMemories(). So
    def blankMyLockyBits(self):
        if self.northSidings:
            self.northSidings = None
        else:
            self.northSidings = False
        if self.northTrackLink:
            self.northTrackLink = None
        else:
            self.northTrackLink = False
        if self.southSidings:
            self.southSidings = False
        if self.southTrackLink:
            self.southTrackLink = False
        self.writeMemories()
        return False

    # Checks this lock against the values of the corresponding memories
    # held by JMRI. If a difference is found we set our variable to False
    # which means the other loco's address does not get overwritten
    # by our writeMemories and after checking everything we call
    # blankMyLockyBits() which sets whatever we did hold to None.
    def checkLock(self):
        self.readMemories()
        err = False
        if self.northSidings:
            if self.northSidingsVal is not None:
                self.northSidings = False
                err = True
        if self.northTrackLink:
            if self.northTrackLinkVal is not None:
                self.northTrackLink = False
                err = True
        if self.southSidings:
            if self.southSidingsVal is not None:
                self.southSidings = False
                err = True
        if self.southTrackLink:
            if self.southTrackLinkVal is not None:
                self.southTrackLink = False
                err = True
        if err:
            self.blankMyLockyBits()
            return False
        return True






















