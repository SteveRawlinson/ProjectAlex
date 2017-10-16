import sys
sys.path.append('C:\\Users\\steve\\Documents\\Github\\JMRI')
import jmri as jmri
import time
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import loco
import java
from javax.swing import JOptionPane
from jmri_bindings import *
from myroutes import *
import track

# import journey classes
from class150Nth2SthTrack1Stopping import *
from class150Sth2NthTrack2Stopping import *
from class150Sth2NthTrack4Stopping import *
from class150Nth2SthTrack3Stopping import *

# DCC_ADDRESSES = [68, 5144, 2144, 6022, 3213, 1087]
DCC_ADDRESSES = [5144, 2144]
DEBUG = True

NORMAL = 0
STOPPING = 1
ESTOP = 2

class Jack(jmri.jmrit.automat.AbstractAutomaton):
    
    def init(self):
        self.locos = [] # array of Loco
        self.tracks = [] # keeping  track of tracks
        self.memories = [] # list of names of  active journeys
        self.status = NORMAL
        self.lastJourneyStartTime = time.time() - 300 # 5 minutes ago

    def debug(self, message):
        if DEBUG:
            print "Jack:", message

    # Creates a Loco object for each DDC address listed above, and
    # gets a location for it.
    def initLocos(self):
        # go through each dcc address
        for a in DCC_ADDRESSES:
            self.debug("setting up loco addr " + str(a))
            # create the Loco object
            newloco = loco.Loco(a)
            self.locos.append(newloco)
            # we get a throttle for the loco here because Loco does
            # not have4 access to getThrottle
            throttleAttempts = 0
            while throttleAttempts < 2 and newloco.throttle is None:
                time.sleep(5)
                newloco.throttle = self.getThrottle(newloco.dccAddr, newloco.longAddr())
                throttleAttempts += 1
            if newloco.throttle is None:
                raise RuntimeError("failed to get a throttle for " + newloco.name())
            self.debug("throttle is set, type is " + type(newloco.throttle).__name__)
            newloco.emergencyStop()

        # get the block & facing direction for each loco
        noBlocks = []
        for newloco in self.locos:
            self.debug("initialising blocks for new loco " + newloco.name())
            # get the block this loco occupies
            b = newloco.initBlock()
            # if no block, prompt user
            if b is None:
                # get a list of occupied blocks with no values
                blist = ['not in use']
                for blockName in (NORTH_SIDINGS + SOUTH_SIDINGS):
                    blk = blocks.getBlock(blockName)
                    if blk.getState() == OCCUPIED and (blk.getValue() is None or blk.getValue() == ""):
                        blist.append(blockName)
                # put up a dropbox for the user to select the block
                self.debug("getting block from user")
                b = JOptionPane.showInputDialog(None,
                                                "Select starting block for " + newloco.name(),
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
                    newloco.setBlock(b)

            elif b == 'multi':
                raise RuntimeError("loco", a, "is in more than one block")
            if newloco.block is None:
                # add to a list to be removed from this operating session
                noBlocks.append(newloco)
            elif newloco.reversible() is False:
                # check it's pointing the right way
                self.debug("getting direction from user")
                b = JOptionPane.showConfirmDialog(None, "Confirm Loco direction", "Loco is facing the right way?", JOptionPane.YES_NO_OPTION)
                if b == JOptionPane.YES_OPTION:
                    newloco.wrongway = False
                else:
                    newloco.wrongway = True
            else:
                # can't be facing the wrong way, since reversible is true
                newloco.wrongway = False


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

    def locosSouth(self):
        southList = []
        for l in self.locos:
            if self.southSidings(l):
                southList.append(l)
        return southList

    # checks for the presence and value of a special memory which
    # can be modified by the user to tell us to stop all activity
    def checkStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        v = mem.getValue()
        self.debug("status memory value: " + str(v) + " type: " + type(v).__name__)
        if v is None or v == "":
            self.debug("setting memory status to " + str(self.status))
            mem.setValue(self.status)
        else:
            self.status = int(mem.getValue())
            self.debug("reading new status from status memory: " + str(self.status))

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
            train = 'loco' + str(loco.dccAddr)
        dir = track.dir()
        tracknr = 'Track' + str(track.nr)
        if loco.passenger():
            stopping = 'Stopping'
        else:
            stopping = 'NonStop'
        return train + dir + tracknr + stopping


    # This is the method that starts new journeys. It is called as part
    # of the main loop, once every second.
    def startNewJourneys(self):
        runningCount = len(self.memories)
        if self.status == STOPPING:
            # no new journeys
            return
        if runningCount > 4:
            # enough activity for now, return
            # TODO: turn trains round?
            return
        if time.time() - self.lastJourneyStartTime < 10.0:
            # too soon since last journey started
            # TODO: turn trains around?
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
        # decide whether to start another journey at all
        if runningCount < 3:
            prob = 1.0
        elif runningCount == 3:
            prob = 0.3
        else:
            prob = 0.1
        end
        if random.random() > prob:
            self.debug("randomly deciding not to start a new journey")
            return
        # pick a loco
        candidates = []
        for loc in self.locos:
            if loc.active():
                continue
            if loc.wrongway is True:
                continue
            candidates.append(loc)





    def startJourney(self, loc, trak):
        klassName = self.constructClassName(loc, trak)
        self.debug("classname: " + klassName)
        klass = globals()[klassName]
        self.debug("klass: " + type(klass).__name__)
        mem = 'IM' + '-'.join(['journey', str(loc.dccAddr), str(trak.nr), trak.dir()]).upper()
        self.debug("startJourney: starting new journey: " + str(loc.dccAddr) + " heading " + trak.dir() + " on track "
                   + str(trak.nr) + " (occupancy: " + str(trak.occupancy) + " busy: " + str(trak.busy()) + " score: " + str(trak.score(loc)) + ") classname: " + klassName + " mem: " + mem)
        memory = memories.provideMemory(mem)
        memory.setValue(1)
        memory.setUserName("Journey " + str(loc.dccAddr) + ' ' + trak.dir() + " on track " + str(trak.nr))
        self.memories.append(memory.getSystemName())
        self.debug("startJourney: set memory " + mem + " value to 1: memory value: " + str(memory.getValue()))
        self.debug("klass: " + type(klass).__name__)
        klass(loc, mem).start()
        loc.status = loco.MOVING
        trak.occupancy += 1
        self.lastJourneyStartTime = time.time()


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

        # Initialise tracks
        self.initTracks()

        # Initialise locomotives and get their location.
        cont = self.initLocos()
        if cont is False:
            # User cancelled
            print "Jack exiting on user cancel"
            return False

        # clear locks
        for lock in ['North Link Lock', 'South Link Lock']:
            self.debug('unlocking ' + lock)
            memories.getMemory(lock).setValue(None)

        # give the sensors time to wake up if we just turned power on
        if poweredOn:
            time.sleep(5)

        # Main Loop
        maxloops = 50
        loopcount = 0
        while True:
            loopcount += 1
            self.debug("loop " + str(loopcount))
            self.checkStatus() # see if we should be stopping
            if self.status == ESTOP:
                # Stop everything immediately
                self.eStop()
                print "Jack exits on ESTOP"
                return False
            self.checkJourneys()
            if self.status == STOPPING and len(self.memories) == 0:
                # We are doing a graceful stop and all journeys are done
                print "All done - exiting"
                return False
            self.startNewJourneys() # kick off new journeys, if appropriate
            if loopcount > maxloops:
                self.debug('exiting after ' + str(maxloops) + ' loops')
                return False # stop the loop for the moment
            time.sleep(10)

        # klassName = "Loco2144Sth2NthTrack2"
        # #klassName = "Loco2144Nth2SthTrack1"
        # constructor = globals()[klassName]
        # self.startJourney(self.locos[0], constructor, mem)
        #
        # time.sleep(5)
        # print "Jack continues"
        # print "loco", self.locos[0].dccAddr, "status is", self.locos[0].status
        # print "Jack exits"

Jack().start()
