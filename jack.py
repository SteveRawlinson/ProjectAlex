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

# DCC_ADDRESSES = [68, 5144, 2144, 6022, 3213, 1087]
#DCC_ADDRESSES = [5144, 2144, 68, 5004]
DCC_ADDRESSES = [3144, 2144]
DEBUG = True


class Jack(jmri.jmrit.automat.AbstractAutomaton):
    
    def init(self):
        self.locos = [] # array of Loco
        self.tracks = [] # keeping  track of tracks
        self.memories = [] # list of names of  active journeys
        self.status = NORMAL
        self.lastJourneyStartTime = time.time() - 300 # 5 minutes ago
        self.status = NORMAL

    def debug(self, message):
        if DEBUG:
            print "Jack:", message

    # Gets a DCC throttle for the loco supplied
    def getLocoThrottle(self, loc):
        throttleAttempts = 0
        while throttleAttempts < 2 and loc.throttle is None:
            time.sleep(5)
            loc.throttle = self.getThrottle(loc.dccAddr, loc.longAddr())
            throttleAttempts += 1
        if loc.throttle is None:
            raise RuntimeError("failed to get a throttle for " + loc.name())

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
        for blockName in (NORTH_SIDINGS + SOUTH_SIDINGS + [NORTH_REVERSE_LOOP, SOUTH_REVERSE_LOOP]):
            blk = blocks.getBlock(blockName)
            if blk.getState() == OCCUPIED and (blk.getValue() is None or blk.getValue() == ""):
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
        if loc.reversible() is False:
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

    # Initialises the tracks[] array, according to information in the myroutes.py file
    def initTracks(self):
        for t in TRACKS:
            tr = track.Track(len(self.tracks) + 1, t[0], t[1], t[2], t[3])
            self.tracks.append(tr)
            print "New track: " + str(tr.nr) + " stops: " + str(tr.stops) + " fast: " + str(tr.fast)

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
                self.debug("track " + str(trak.nr) + " occupancy is now " + str(trak.occupancy))
                mems_to_delete.append(m)
        # Remove the memories corresponding to the journeys
        # that have no finished
        for m in mems_to_delete:
            self.memories.remove(m)


    def northBoundTrack(self, track):
        return track.nr % 2 == 0

    def southBoundTrack(self, track):
        return not self.northBoundTrack(track)

    # Makes a guess at the class name that should describe the
    # journey for this loco on this track.
    def constructClassName(self, loco, track):
        if loco.brclass() is not None:
            train = 'Class' + str(loco.brclass())
        else:
            train = 'Loco' + str(loco.dccAddr)
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
        runningCount = len(self.memories)
        if self.status == STOPPING:
            # no new journeys
            return
        if runningCount > 5:
            # enough activity for now, return
            # TODO: turn trains round?
            return
        if runningCount == 1 and time.time() - self.lastJourneyStartTime < 30.0:
            # we're just starting up, stagger first two journeys
            return
        # Find idle locos with 0 rarity and get them moving if possible
        for loc in self.locos:
            if loc.rarity() > 0:
                continue
            if loc.active():
                continue
            self.debug("found idle loco with rarity 0: " + loc.name())
            # get this loco moving if possible
            trak = track.Track.preferred_track(loc, self.tracks)
            if trak is not None:
                self.debug("selected track " + str(trak.nr) + " for loco " + str(loc.dccAddr) + " score: " + str(trak.score(loc)))
                self.startJourney(loc, trak)
                return
            else:
                self.debug("no available tracks to run loco " + loc.name())
        if time.time() - self.lastJourneyStartTime < 10.0:
            # too soon since last journey started
            # TODO: turn trains around?
            return
        # decide whether to start another journey at all
        if runningCount < 3:
            prob = 1.0
        elif runningCount == 3:
            prob = 0.5
        else:
            prob = 0.3
        if random.random() > prob:
            self.debug("randomly deciding not to start a new journey (running count: " + str(runningCount) + ")")
            return
        # Pick a loco to start up. This is done on the basis of the
        # available loco's rarity value - prefer non rare locos
        #self.debug("picking a loco")
        # get a list of candidate locos
        candidates = []
        for loc in self.locos:
            if loc.active():
                continue
            if loc.wrongway is True:
                continue
            if loc.northSidings() and track.Track.southboundTracksFree(self.tracks) == 0:
                continue
            if loc.southSidings() and track.Track.northboundTracksFree(self.tracks) == 0:
                continue
            if loc.reversible() is False and loc.northSidings() and isBlockOccupied(SOUTH_REVERSE_LOOP) is True:
                # the reverse loop is occupied and we don't know by what
                continue
            if loc.reversible() is False and loc.southSidings() and isBlockOccupied(NORTH_REVERSE_LOOP) is True:
                # the reverse loop is occupied and we don't know by what
                continue
            candidates.append(loc)
        # pick one according to rarity
        if len(candidates) == 0:
            #self.debug("no locos available to start a new journey")
            return
        tot = 0.0
        for c in candidates:
            tot += (1 - c.rarity())
        n = tot * random.random()
        for c in candidates:
            n -= (1 - c.rarity())
            if n < 0.0:
                loc = c
                break
        self.debug("picked loco " + str(loc.dccAddr) + " status: " + str(loc.status))
        # pick a track
        trak = track.Track.preferred_track(loc, self.tracks)
        if trak is not None:
            self.debug("selected track " + str(trak.nr) + " for loco " + str(loc.dccAddr) + " score: " + str(trak.score(loc)))
            self.startJourney(loc, trak)
            return
        else:
            self.debug("no available tracks to run loco " + loc.name())
            if DEBUG:
                track.Track.trackReport(self.tracks)



    # Actually kick off a new journey using the loco and track supplied
    def startJourney(self, loc, trak):
        # get the appropriate classname
        klassName = self.constructClassName(loc, trak)
        self.debug("classname: " + klassName)
        # get the class
        klass = globals()[klassName]
        # set the memory name
        mem = 'IM' + '-'.join(['journey', str(loc.dccAddr), str(trak.nr), trak.dir()]).upper()
        self.debug("startJourney: starting new journey: " + str(loc.dccAddr) + " heading " + trak.dir() + " on track "
                   + str(trak.nr) + " (occupancy: " + str(trak.occupancy) + " busy: " + str(trak.busy()) + " score: " + str(trak.score(loc)) + ") classname: " + klassName + " mem: " + mem)
        # set the memory value
        memory = memories.provideMemory(mem)
        memory.setValue(1)
        memory.setUserName("Journey " + str(loc.dccAddr) + ' ' + trak.dir() + " on track " + str(trak.nr))
        # add memory to lisr
        self.memories.append(memory.getSystemName())
        # kick the journey off
        klass(loc, mem).start()
        loc.status = loco.MOVING
        trak.occupancy += 1
        self.lastJourneyStartTime = time.time()


    # Checks a memory for a value, if there is one, adds a loco
    # to the list by prompting the user for a dcc address
    def checkForNewLocos(self):
        m = memories.provideMemory("IMNEWLOCO")
        if m.getValue() is not None and m.getValue() != "" and m.getValue() != 0:
            addr = JOptionPane.showInputDialog("DCC address of new loco:")
            self.debug("joptionpane returned " + str(addr) + " type " + type(addr).__name__)
            if addr != "" and addr is not None and int(addr) > 0:
                loc = self.getNewLoco(int(addr))
                self.getLocoThrottle(loc)
                loc.emergencyStop()
                b = loc.initBlock()
                if b is None:
                    if self.getBlockOccupiedByLocoFromUser(loc) is not False:
                        if loc.block is not None:
                            self.locos.append(loc)
            m.setValue(None)
            sen = sensors.getSensor("Add Loco")
            sen.setKnownState(INACTIVE)


    def handle(self):
        self.debug("Jack Starting")

        # set status memory variable
        self.setStatus()

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
        for lock in ['North Link Lock', 'South Link Lock']:
            self.debug('unlocking ' + lock)
            mem = memories.getMemory(lock)
            if mem is not None:
                mem.setValue(None)

        # set sensors to inactive
        for s in ["Add Loco", "Stop", "Estop"]:
            sen = sensors.getSensor(s)
            sen.setKnownState(INACTIVE)

        # reset memories
        for m in ["IMNEWLOCO"]:
            mem = memories.getMemory(m)
            mem.setValue(None)

        # Initialise tracks
        self.initTracks()

        # Initialise locomotives and get their location.
        cont = self.initLocos()
        if cont is False:
            # User cancelled
            print "Jack exiting on user cancel"
            return False

        # give the sensors time to wake up if we just turned power on
        if poweredOn:
            time.sleep(5)

        # final status check before we hit main loop
        if self.checkStatus() != NORMAL:
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
                self.eStop()
                print "Jack exits on ESTOP"
                return False
            # check for journeys that have completed
            self.checkJourneys()
            if self.status == STOPPING and len(self.memories) == 0:
                # We are doing a graceful stop and all journeys are done
                print "All done - exiting"
                return False
            # kick off new journeys, if appropriate
            self.startNewJourneys()
            # check for new locos
            self.checkForNewLocos()
            # bow out if there's a limit
            if maxloops is not None and loopcount > maxloops:
                self.debug('exiting after ' + str(maxloops) + ' loops')
                self.status = STOPPING
                self.setStatus()
                return False # stop the loop for the moment

            time.sleep(1)
        # ------------ end main loop -------------------

Jack().start()
