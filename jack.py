import sys
sys.path.append('C:\\Users\\steve\\Documents\\Github\\JMRI')
import jmri as jmri
import time
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
sys.path.append('/Users/steve/src/ProjectAlex')
import loco
import java
from javax.swing import JOptionPane
from jmri_bindings import *
from myroutes import *
import track
import random
import util
import datetime
import os
import os.path

# import journey classes
from class150Nth2SthTrack1Stopping import *
from class150Sth2NthTrack2Stopping import *
from class150Sth2NthTrack4Stopping import *
from class150Nth2SthTrack3Stopping import *
from classA4Nth2SthTrack1Stopping import *
from classA4Sth2NthTrack2Stopping import *
from classA4Nth2SthTrack3Stopping import *
from classA4Sth2NthTrack4Stopping import *
from classFastSth2NthTrack6Nonstop import *
from classFastNth2SthTrack5Nonstop import *
from classAnyNth2SthTrack1Nonstop import *
from classAnySth2NthTrack2Nonstop import *
from classAnyNth2SthTrack3Nonstop import *
from classAnySth2NthTrack4Nonstop import *
from classAnyNth2SthTrack5 import *
from classAnySth2NthTrack6 import *
from classAnyNorthLinkToNorthSidings import *
from moveLocoToSidings import *

#DCC_ADDRESSES = [68, 2128, 2144, 7405, 1087]
#DCC_ADDRESSES = [2144, 2128]
#DCC_ADDRESSES = [2128, 2144, 1124, 5004, 1087, 3213]
#DCC_ADDRESSES = [1124]
#DCC_ADDRESSES = [6719]
#DCC_ADDRESSES = [7405]
#DCC_ADDRESSES = [1124]
#DCC_ADDRESSES = [3213]
#DCC_ADDRESSES = [5004, 1124, 3213, 6719, 1087, 2144, 2128, 68, 7405] # full set
#DCC_ADDRESSES = [2144, 2128, 4030]
DCC_ADDRESSES = [2144, 2128, 1087, 3213, 7405, 4404, 6719, 5004, 4030]
#DCC_ADDRESSES = []
DEBUG = True


# This is the class that does the orchestration of the whole automated
# process.

class Jack(util.Util, jmri.jmrit.automat.AbstractAutomaton):
    
    def init(self):
        self.locos = []        # array of Loco
        self.retiredlocos = [] # array of locos we were using but not any more
        self.tracks = []       # keeping  track of tracks
        self.memories = []     # list of names of  active journeys
        self.status = NORMAL
        self.lastJourneyStartTime = time.time() - 300 # 5 minutes ago
        self.status = NORMAL

    def debug(self, message):
        calling_method = sys._getframe(1).f_code.co_name
        if DEBUG:
            print str(datetime.datetime.now()) + ' ' + "Jack: " + calling_method + ': ' + message
            self.log(message)

    # Gets a DCC throttle for the loco supplied
    def getLocoThrottle(self, loc):
        throttleAttempts = 0
        while throttleAttempts < 2 and loc.throttle is None:
            loc.throttle = self.getThrottle(loc.dccAddr, loc.longAddr())
            if loc.throttle is None:
                throttleAttempts += 1
                time.sleep(5)
        if loc.throttle is None:
            raise RuntimeError("failed to get a throttle for " + loc.name())
        slot = loc.throttle.getLocoNetSlot()
        if slot:
            self.debug("got throttle for loco addr " + str(loc.dccAddr) + " slot " + str(slot.getSlot()) + " status: " + LN_SLOT_STATUS[slot.slotStatus()])
        else:
            self.debug("throttle for loco addr " + str(loc.dccAddr) + " has no slot ")


    # gets a new loco and appends it to self.locos
    def getNewLoco(self, addr):
        self.debug("setting up loco addr " + str(addr))
        # create the Loco object
        newloco = loco.Loco(addr)
        self.locos.append(newloco)
        return newloco

    def getBlockOccupiedByLocoFromUser(self, loc):
        # get a list of occupied blocks with no values
        blist = ['not in use']
        for blockName in (SOUTH_SIDINGS + NORTH_SIDINGS +  [NORTH_REVERSE_LOOP, SOUTH_REVERSE_LOOP, 'North Link']):
            blk = blocks.getBlock(blockName)
            if blk.getState() != OCCUPIED:
                continue
            if blk.getValue() is not None and  blk.getValue() != "":
                continue
            blist.append(blockName)
        # put up a dropbox for the user to select the block
        self.debug("getting block from user")
        b = JOptionPane.showInputDialog(None,
                                        "Select starting block for " + loc.nameAndAddress(),
                                        "Choose block",
                                        JOptionPane.QUESTION_MESSAGE,
                                        None,
                                        blist,
                                        'not in use')
        if b is None:
            # User cancelled
            return False
        if b != "not in use":
            # set the block
            loc.setBlock(b)
        elif b == 'multi':
            raise RuntimeError("loco", loc.nameAndAddress(), "is in more than one block")

    def confirmLocoDirection(self, loc):
        if loc.reversible() is False and loc.inReverseLoop() is False:
            # check it's pointing the right way
            self.debug("getting direction from user")
            b = JOptionPane.showConfirmDialog(None, "Loco " + str(loc.nameAndAddress()) + " is facing the right way?",
                                              "Confirm Loco direction", JOptionPane.YES_NO_OPTION)
            if b == JOptionPane.YES_OPTION:
                loc.wrongway = False
            else:
                loc.wrongway = True
        else:
            # can't be facing the wrong way, since reversible is true
            loc.wrongway = False

    # Creates a Loco object for each DDC address listed above, and
    # gets a location for it.
    def initLocos(self):
        # go through each dcc address
        for a in DCC_ADDRESSES:
            newloco = self.getNewLoco(a)
            self.debug("initialised loco " + newloco.nameAndAddress() + " decoder family " + newloco.decoderFamily())
            self.getLocoThrottle(newloco)
            newloco.emergencyStop()
        # get the block & facing direction for each loco
        noBlocks = []
        for newloco in self.locos:
            self.debug("initialising blocks for new loco " + newloco.name())
            # get the block this loco occupies
            b = newloco.initBlock()
            # if no block, prompt user
            if b is None:
                if self.getBlockOccupiedByLocoFromUser(newloco) is False:
                    # User pressed 'cancel'
                    return False # abort
            if newloco.block is None:
                # add to a list to be removed from this operating session
                noBlocks.append(newloco)
            else:
                self.confirmLocoDirection(newloco)
        # remove locos that have no block
        for l in noBlocks:
            self.locos.remove(l)


    # Returns True if the loco supplied is in the north sidings
    def northSidings(self, loc):
        return loc.northSidings

    # Returns True is the loco supplied in south sidings
    def southSidings(self, loc):
        return loc.southSidings

    # def locosSouth(self):
    #     southList = []
    #     for l in self.locos:
    #         if self.southSidings(l):
    #             southList.append(l)
    #     return southList

    # checks for the presence and value of a special memory which
    # can be modified by the user to tell us to stop all activity
    def checkStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        v = mem.getValue()
        # self.debug("status memory value: " + str(v) + " type: " + type(v).__name__)
        if v is None or v == "":
            self.debug("setting memory status to " + str(self.status))
            mem.setValue(self.status)
        else:
            self.status = int(mem.getValue())
            #self.debug("reading new status from status memory: " + str(self.status))
        return self.status

    def setStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        mem.setValue(self.status)

    # stop all locos immediately
    def eStop(self):
        for loc in self.locos:
            loc.emergencyStop()

    # Checks if any journeys have completed since the last check
    # and decrement the loco count on the track. Also remove the
    # memory from our list of memories
    def checkJourneys(self):
        if len(self.memories) == 0:
            return
        mems_to_delete = []
        for m in self.memories:
            mem = memories.provideMemory(m)
            if int(mem.getValue()) != 1:
                # Journey has finished
                self.debug("journey " + mem.getDisplayName() + " has finished")
                journey, addr, tracknr, dir = m.split('-')
                # get the track object
                trak = self.tracks[int(tracknr) - 1]
                # reduce the occupancy
                trak.occupancy -= 1
                self.debug("track " + str(trak.nr) + " occupancy reduced to " + str(trak.occupancy))
                # update the last used time
                trak.last_used = time.time()
                #self.debug("track " + str(trak.nr) + " occupancy is now " + str(trak.occupancy))
                mems_to_delete.append(m)
        # Remove the memories corresponding to the journeys
        # that have no finished
        for m in mems_to_delete:
            self.memories.remove(m)


    # Makes a guess at the class name that should describe the
    # journey for this loco on this track.
    def constructClassName(self, loco, track=None, ending=None):
        if loco.brclass() is not None:
            train = 'Class' + str(loco.brclass())
        else:
            train = 'Loco' + str(loco.dccAddr)
        if ending:
            return train + ending
        if track is None:
            raise RuntimeError("track must be specified if ending is None")
        dir = track.dir()
        tracknr = 'Track' + str(track.nr)
        if loco.passenger():
            stopping = 'Stopping'
        else:
            stopping = 'Nonstop'
        return train + dir + tracknr + stopping


    # This is the method that starts new journeys. It is called as part
    # of the main loop, once every second.
    def startNewJourneys(self):
        # wait until the power comes back on
        if powermanager.getPower() == jmri.PowerManager.OFF:
            return
        runningCount = len(self.memories)
        if self.status == STOPPING:
            # no new journeys
            return
        if runningCount > 5:
            # enough activity for now, return
            # TODO: turn trains round?
            return
        # check for retired locos not in sidings
        # for l in self.retiredlocos:
        #     if l.block.getUserName() not in NORTH_SIDINGS + SOUTH_SIDINGS + [NORTH_REVERSE_LOOP, SOUTH_REVERSE_LOOP]:
        #         MoveLocoToSidings(l, None, None).start()
        #         if l in self.retiredlocos:
        #             self.retiredlocos.remove(l)
        #         return
        # Find idle locos with 0 rarity and get them moving if possible
        for loc in self.locos:
            if loc.rarity() > 0:
                continue
            if loc.active():
                continue
            self.log("found idle loco with rarity 0: " + loc.nameAndAddress())
            # get this loco moving if possible
            trak = track.Track.preferred_track(loc, self.tracks)
            if trak is not None:
                self.debug("selected track " + str(trak.nr) + " for loco " + str(loc.dccAddr) + " score: " + str(trak.score(loc)))
                self.startJourney(loc, trak)
                return
            else:
                self.log("no available tracks to run loco " + loc.name())
                # if this loco has stopped early on North Link we need to move it to
                # sidings to get it out the way
                if loc.block.getUserName() == 'North Link':
                    self.debug("moving loco off North Link into sidings because there are no available tracks to run it")
                    klassName = self.constructClassName(loc, None, ending='NorthLinkToNorthSidings')
                    loc.status = loco.ACTIVE
                    self.startJourney(loc, None, klassName=klassName)
                    return
        if time.time() - self.lastJourneyStartTime < 10.0:
            # too soon since last journey started
            # TODO: turn trains around?
            return

        # decide whether to start another journey at all
        startNewJourney = False
        if runningCount < 2:
            # always get 2 journeys going
            prob = 1.0
        elif runningCount == 2:
            # a third journey every 20 secs
            prob = 0.05
        else:
            # a 4th journey every min of 3 running
            prob = 0.02
        randomNumber = random.random()
        self.log("randomNumber: " + str(randomNumber) + " prob: " + str(prob) + " running count: " + str(runningCount))
        if randomNumber > prob:
            self.log ("not starting a new journey (unless a preferred loco is found)")
        else:
            self.log("starting new journey")
            startNewJourney = True

        # Pick a loco to start up. This is done on the basis of the
        # available loco's rarity value - prefer non rare locos.

        # get a list of candidate locos even if startNewJourney is False: a
        # preferred_loco means we should really get that one going regardless
        candidates = []
        preferred_loco = None
        self.log("selecting loco from list of " + str(len(self.locos)))
        # log the track conditions
        s = track.Track.trackReport(self.tracks)
        for l in iter(s.splitlines()):
            self.log(l)
        # check if we have any locos in sidings - useful later
        locosInNorthSidings = False
        if self.locoCountInSidings(self.locos, NORTH_SIDINGS) > 0:
            self.log("we have locos in North Sidings")
            locosInNorthSidings = True
        locosInSouthSidings = False
        if self.locoCountInSidings(self.locos, SOUTH_SIDINGS) > 0:
            self.log("we have locos in South Sidings")
            locosInSouthSidings = True
        for loc in self.locos:
            self.log("considering " + loc.nameAndAddress() + " in " + loc.block.getUserName())
            if loc.active():
                if loc.reversible() is False:
                    # check if non-reversible loco is heading towards occupied reverse loop
                    if loc.dir() == 'Nth2Sth':
                        oloop = SOUTH_REVERSE_LOOP
                    else:
                        oloop = NORTH_REVERSE_LOOP
                    addr = self.isBlockOccupied(oloop)
                    if addr is not False and addr is not True:
                        # must be the address of the loco in the loop, remember it for later
                        preferred_loco = loco.Loco.getLocoByAddr(addr, self.locos)
                        self.log("  setting preferred loco to " + preferred_loco.nameAndAddress())
                continue
            # don't run non-reversible locos in sidings facing the wrong way
            if loc.wrongway is True:
                self.log("  wrongway is true")
                continue
            # don't run locos with no free tracks
            if loc.northSidings() and track.Track.southboundTracksFree(self.tracks) == 0:
                self.log("  there are no free southbound tracks")
                continue
            if loc.southSidings() and track.Track.northboundTracksFree(self.tracks) == 0:
                self.log("  there are no free northbound tracks")
                continue
            # don't pick a loco if there are no free sidings on the other side (pick one from that side instead)
            if (loc.northSidings() or loc.inReverseLoop()) and self.freeSidingCount(SOUTH_SIDINGS) == 0 and locosInSouthSidings:
                self.log("  there are no free sidings in South Sidings")
                continue
            if (loc.southSidings() or loc.inReverseLoop()) and self.freeSidingCount(NORTH_SIDINGS) == 0 and locosInNorthSidings:
                self.log("  there are no free sidings in North Sidings")
                continue
            # Don't pick a loco if there are way more locos on the other side
            if (loc.southSidings() or loc.inReverseLoop()) and self.freeSidingCount(SOUTH_SIDINGS) - self.freeSidingCount(NORTH_SIDINGS) > 2:
                self.log("  there are way more locos in north sidings")
                continue
            if (loc.northSidings() or loc.inReverseLoop()) and self.freeSidingCount(NORTH_SIDINGS) - self.freeSidingCount(SOUTH_SIDINGS) > 2:
                self.log("  there are way more locos in south sidings")
                continue
            # If there are no tracks available for this loco, don't pick it
            if track.Track.preferred_track(loc, self.tracks) is None:
                self.log("  there are no tracks available")
                continue
            # don't run non-reversible locos if the opposite reverse loop is occupied by an unknown thing
            if loc.reversible() is False:
                if loc.northSidings():
                    oppositeLoc = self.isBlockOccupied(SOUTH_REVERSE_LOOP)
                else:
                    oppositeLoc = self.isBlockOccupied(NORTH_REVERSE_LOOP)
                if oppositeLoc is True:
                    self.log("  an unknown loco is in the Opposite Reverse Loop")
                    continue
                # don't run non-reversible locos in the loco in the opposite reverse loop has no tracks available
                if oppositeLoc:
                    # it's a loco we know about
                    if track.Track.preferred_track(loc, self.tracks) is None:
                        self.log("  there are no tracks available for the loco in the opposite reverse loop")
                        continue
            # add this loco to the list of candidates
            self.log("  adding loco to candidates")
            candidates.append(loc)

        # bale out now if we are not starting a new journey
        if startNewJourney is False and preferred_loco is None:
            self.log("no preferred loco, not starting new journey")
            return

        self.log("we have " + str(len(candidates)) + " candidates")
        if len(candidates) == 0:
            self.log("no candidates, returning")
            return
        # if we have a preferred loco, and it's in the candidate list, pick that one
        if preferred_loco is not None and preferred_loco in candidates:
            self.debug("picking preferred loco")
            loc = preferred_loco
        elif startNewJourney:
            # pick one according to rarity
            if len(candidates) == 0:
                #self.debug("no locos available to start a new journey")
                return
            if len(candidates) == 1:
                loc = candidates[0]
            else:
                list = []
                for c in candidates:
                    list.append([c, 1 - c.rarity()])
                loc = Jack.weighted_choice(list)
        else:
            # if we get here it means there was a preferred loco but
            # it wasn't in the list of candidates - bale out
            return

        self.debug("picked loco " + loc.nameAndAddress() + " status: " + str(loc.status))
        #self.log("picked loco " + loc.nameAndAddress() + " status: " + str(loc.status))
        # pick a track
        trak = track.Track.preferred_track(loc, self.tracks)
        if trak is None:
            self.debug("no available tracks to run loco " + loc.name())
            self.log("no available tracks to run loco " + loc.name())
            # if DEBUG:
            #     track.Track.trackReport(self.tracks)
            return
        self.debug("selected track " + str(trak.nr) + " for loco " + str(loc.dccAddr) + " score: " + str(trak.score(loc)))
        self.log("selected track " + str(trak.nr) + " for loco " + str(loc.dccAddr) + " score: " + str(trak.score(loc)))
        self.debug("north sidings free: " + str(self.freeSidingCount(NORTH_SIDINGS)) + " south sidings free: " + str(self.freeSidingCount(SOUTH_SIDINGS)))
        self.startJourney(loc, trak)





    # Actually kick off a new journey using the loco and track supplied
    def startJourney(self, loc, trak, klassName=None):
        if klassName is None:
            # get the appropriate classname
            klassName = self.constructClassName(loc, trak)
        self.debug("classname: " + klassName)
        # get the class
        klass = globals()[klassName]
        if trak:
            # set the memory name
            mem = 'IM' + '-'.join(['journey', str(loc.dccAddr), str(trak.nr), trak.dir()]).upper()
            self.debug("startJourney: starting new journey: " + str(loc.dccAddr) + " heading " + trak.dir() + " on track " + str(trak.nr) + " (occupancy: " + str(trak.occupancy) + " busy: " + str(trak.busy()) + " score: " + str(trak.score(loc)) + ") classname: " + klassName + " mem: " + mem)
            # set the memory value
            memory = memories.provideMemory(mem)
            memory.setValue(1)
            memory.setUserName("Journey " + str(loc.dccAddr) + ' ' + trak.dir() + " on track " + str(trak.nr))
            # add memory to list
            self.memories.append(memory.getSystemName())
            # set memory for the display
            m = memories.provideMemory("IMTRACK" + str(trak.nr) + "LOCO")
            m.setValue(loc.nameAndAddress())
            m = memories.provideMemory("IMTRACK" + str(trak.nr) + "SPEED")
            m.setValue(0)
        else:
            mem = None
        if trak:
            self.debug("setting loco " + loc.nameAndAddress() + " to track " + str(trak.nr))
            loc.track = trak
            trak.occupancy += 1
        else:
            self.debug("no track supplied, not setting")
        # kick the journey off
        klass(loc, mem, trak).start()
        loc.status = loco.MOVING
        self.lastJourneyStartTime = time.time()


    # Checks a memory for a value, if there is one, adds a loco
    # to the list by prompting the user for a dcc address
    def checkForNewLocos(self):
        m = memories.provideMemory("IMNEWLOCO")
        if m.getValue() is not None and m.getValue() != "" and m.getValue() != 0:
            addr = JOptionPane.showInputDialog("DCC address of new loco:")
            if addr != "" and addr is not None and int(addr) > 0:
                loc = self.getNewLoco(int(addr))
                try:
                    loc.rosterEntry()
                except:
                    self.debug("no roster entry for address " + str(addr))
                    # incorrect dcc addr
                    self.locos.remove(loc)
                    del loc
                    return
                try:
                    self.getLocoThrottle(loc)
                except RuntimeError:
                    # idiot at the keyboard entered wrong dcc addr
                    self.locos.remove(loc)
                    del loc
                    return
                loc.emergencyStop()
                b = loc.initBlock()
                if b is None:
                    if self.getBlockOccupiedByLocoFromUser(loc) is not False:
                        if loc.block is not None:
                            self.locos.append(loc)
            m.setValue(None)
            sen = sensors.getSensor("Add Loco")
            sen.setKnownState(INACTIVE)

    # Checks a memory for a value, if there is one, adds a loco
    # to the list by prompting the user for a dcc address
    def checkForRetiringLocos(self):
        m = memories.provideMemory("IMRETIRELOCO")
        if m.getValue() is not None and m.getValue() != "" and m.getValue() != 0:
            # put up a dropbox for the user to select the loco
            b = JOptionPane.showInputDialog(None,
                                            "Select loco to retire",
                                            "Loco to retire",
                                            JOptionPane.QUESTION_MESSAGE,
                                            None,
                                            map(lambda l: l.nameAndAddress(), self.locos),
                                            self.locos[0].nameAndAddress())
            if b is None:
                # User cancelled
                sen = sensors.getSensor("Retire Loco")
                sen.setKnownState(INACTIVE)
                return False
            for l in self.locos:
                if l.nameAndAddress() == b:
                    # found the loco
                    self.debug("retiring loco " + b)
                    # see if this loco is on a journey
                    for m in self.memories:
                        bits = m.split('-')
                        self.debug("bit[1]: " + bits[1])
                        if int(bits[1]) == l.dccAddr:
                            # set a memory so the journey picks it up
                            mem = memories.provideMemory('IMRETIREDLOCO')
                            self.debug("setting IMRETIREDLOCO to value " + str(l.dccAddr))
                            mem.setValue(l.dccAddr)
                        else:
                            self.debug(bits[1] + " != " + str(l.dccAddr))
                    self.locos.remove(l)
                    self.retiredlocos.append(l)
            sen = sensors.getSensor("Retire Loco")
            sen.setKnownState(INACTIVE)


    def checkTrackStatus(self):
        for t in self.tracks:
            t.checkStatus()

    # ------------------------ Main -----------------------------------
    def handle(self):

        self.debug("Jack Starting")

        if self.getJackStatus() != STOPPED:
            # maybe still running?
            b = JOptionPane.showConfirmDialog(None, "Jack might already be running, continue?",
                                              "JackStatus: " + str(self.getJackStatus()), JOptionPane.YES_NO_OPTION)
            if b == JOptionPane.NO_OPTION:
                self.debug("Quitting on user command")
                return False

        # set status memory variable
        self.setStatus()

        # rotate logs
        if os.path.exists(LOGFILE):
            if os.path.exists(LOGFILE + '.6'):
                os.remove(LOGFILE + '.6')
            for i in range(5,0,-1):
                fn = LOGFILE + '.' + str(i)
                if os.path.exists(fn):
                    os.rename(fn, LOGFILE + '.' + str(i+1))
            os.rename(LOGFILE, LOGFILE + '.1')

        # turn layout power on
        self.powerState = powermanager.getPower()
        if self.powerState != jmri.PowerManager.ON:
            poweredOn = True
            self.debug("turning power on")
            powermanager.setPower(jmri.PowerManager.ON)
        else:
            poweredOn = False
            self.debug("power is on")

        # clear locks
        for lock in ['North Link Lock', 'South Link Lock', 'IMLOCKNORTHSIDINGS', 'IMLOCKNORTHTRACKLINK', 'IMLOCKSOUTHSIDINGS', 'IMLOCKSOUTHTRACKLINK']:
            self.debug('unlocking ' + lock)
            mem = memories.getMemory(lock)
            if mem is not None:
                mem.setValue(None)

        # unselect all sidings
        loco.Loco.unselectSidings(NORTH_SIDINGS + SOUTH_SIDINGS)
        loco.Loco.unselectReverseLoops([NORTH_REVERSE_LOOP, SOUTH_REVERSE_LOOP])

        # clear display memories
        for i in range(1,7):
            m = memories.provideMemory("IMTRACK" + str(i) + "LOCO")
            m.setValue(None)
            m = memories.provideMemory("IMTRACK" + str(i) + "SPEED")
            m.setValue(None)

        # set sensors to inactive
        for s in ["Add Loco", "Stop", "Estop"]:
            sen = sensors.getSensor(s)
            sen.setKnownState(INACTIVE)

        # reset memories
        for m in ["IMNEWLOCO", "IMRETIRELOCO", "IMRETIREDLOCO"]:
            mem = memories.getMemory(m)
            if mem is not None:
                mem.setValue(None)

        # Initialise tracks
        self.initTracks()

        # check these sensors are not active, they control lock release
        for s in ["LS60", "LS64"]:
            sen = sensors.getSensor(s)
            if sen.knownState == ACTIVE:
                raise RuntimeError("sensor " + s + " is active")

        # Initialise locomotives and get their location.
        cont = self.initLocos()
        if cont is False:
            # User cancelled
            print "Jack exiting on user cancel"
            self.status = STOPPED
            self.setStatus()
            return False

        # give the sensors time to wake up if we just turned power on
        if poweredOn:
            time.sleep(5)

        # log sensor status
        for n in sensors.getSystemNameList():
            s = sensors.getSensor(n)
            self.log("sensor: " + str(s.getDisplayName()) + " state: " + str(s.state))

        # clear block values in unoccupied blocks
        for name in blocks.getSystemNameList():
            self.log("checking block " + name)
            b = blocks.getBlock(name)
            if b.getState() != OCCUPIED:
                self.log("setting value of block " + name + " to None")
                b.setValue(None)
                if b.getUserName() is not None:
                    m = memories.getMemory(b.getUserName())
                    if m is not None:
                        m.setValue(None)


        # final status check before we hit main loop
        if self.checkStatus() != NORMAL:
            self.status = STOPPED
            self.setStatus()
            self.debug("exiting on non-normal status")
            return False


        print "Jack entering main loop."

        # ------------- Main Loop -------------------
        maxloops = 10000
        loopcount = 0
        while True:
            loopcount += 1
            if loopcount % 100 == 0:
                self.debug("loop " + str(loopcount))
            self.checkStatus() # see if we should be stopping
            if self.status == ESTOP:
                # Stop everything immediately
                self.eStop() # stops all locos
                self.debug("Jack waiting to exit on eStop")
                # give other processes time to read the estop
                time.sleep(30)
                print "Jack exits on ESTOP"
                self.status = STOPPED
                self.setStatus()
                return False
            # check for journeys that have completed
            self.checkJourneys()
            if self.status == STOPPING:
                if len(self.memories) == 0:
                    print "All done - exiting"
                    self.status = STOPPED
                    self.setStatus()
                    return False
                elif loopcount % 20 == 0:
                    self.debug("waiting for " + str(len(self.memories)) + " journeys to complete")
                    for m in self.memories:
                        self.debug('  ' + m)
            # kick off new journeys, if appropriate
            self.startNewJourneys()
            # check for new locos
            self.checkForNewLocos()
            # check for locos to retire
            self.checkForRetiringLocos()
            # check to see if track status has changed
            self.checkTrackStatus()
            # bow out if there's a limit
            if maxloops is not None and loopcount > maxloops:
                self.debug('exiting after ' + str(maxloops) + ' loops')
                self.status = STOPPED
                self.setStatus()
                return False # stop the loop for the moment

            time.sleep(1)
        # ------------ end main loop -------------------

Jack().start()
