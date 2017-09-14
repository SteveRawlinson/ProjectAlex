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

# DCC_ADDRESSES = [68, 5144, 2144, 6022, 3213, 1087]
DCC_ADDRESSES = [2144]
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
            self.debug("initialising blocks for new loco " + newloco.name())
            # get the block this loco occupies
            b = newloco.initBlock()
            # if no block, prompt user
            if b is None:
                # get a list of occupied blocks with no values
                blist = ['not in use']
                for blockName in (NORTH_SIDINGS + SOUTH_SIDINGS):
                    #self.debug("checking block " + blockName)
                    blk = blocks.getBlock(blockName)
                    if blk.getState() == OCCUPIED and (blk.getValue() is None or blk.getValue() == ""):
                        #self.debug("adding " + blockName + " to blist")
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
                if b != "not in use":
                    # set the block and add the new loco to the list
                    newloco.setBlock(b)

            elif b == 'multi':
                raise RuntimeError("loco", a, "is in more than one block")
            if newloco.block is not None:
                self.locos.append(newloco)

    # Initialises the tracks[] array, according to information in the myroutes.py file
    def initTracks(self):
        for t in TRACKS:
            tr = track.Track(len(self.tracks) + 1, t[0], t[1])
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

    def startJourney(self, loc, klass, mem):
        loc = self.locos[0]
        trak = self.tracks[0]
        mem = '-'.join(['journey', str(loc.dccAddr), str(trak.nr), trak.dir()])
        klass = globals()['Class150Nth2SthTrack1Stopping']
        memory = memories.provideMemory(mem)
        memory.setValue(1)
        self.debug("startJourney: set memory " + mem + " value to 1: memory value: " + str(memory.getValue()))
        klass(loc, mem).start()
        loc.status = loco.MOVING
        trak.occupancy += 1

    # checks for the presence and value of a special memory which
    # can be modified by the user to tell us to stop all activity
    def checkStatus(self):
        mem = memories.provideMemory('JackStatus')
        if mem.getValue() == "":
            mem.setValue(self.status)
        else:
            self.status = mem.getValue()

    # stop all locos immediately
    def eStop(self):
        for loc in self.locos:
            loc.emergencyStop()

    # Checks if any journeys have completed since the last check
    # and decrement the loco count on the track. Also remove the
    # memory from our list of memories
    def checkJourneys(self):
        mems_to_delete = []
        for m in self.memories:
            self.debug("checkJourneys: checking memory " + m)
            mem = memories.provideMemory(m)
            if mem.getValue() != 1:
                # Journey has finished
                self.debug("journey " + mem + " has finished")
                journey, addr, tracknr, dir = m.split('-')
                # get the track object
                trak = self.tracks[int(tracknr) - 1]
                # reduce the occupancy
                trak.occupancy -= 1
                # update the last used time
                trak.last_used = time.time()
                self.debug("track " + trak.nr + " occupancy is now " + str(trak.occupancy))
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


    def startNewJourneys(self):
        if self.status == STOPPING:
            # no new journeys
            return
        if len(self.memories) > 5:
            # enough activity for now, return
            # TODO: turn trains round?
            return
        # Find idle locos with 0 rarity and get them moving if possible
        for loc in self.locos:
            if loc.rarity() > 0:
                continue
            if loc.active():
                continue
            self.debug("found idle loco with rarity 0: " + loc.name)
            # get this loco moving if possible
            trak = track.Track.preferred_track(loc, self.tracks)
            if trak is not None:
                klassName = self.constructClassName(loc, trak)
                self.debug("classname: " + klassName)
                klass = globals()[klassName]
                mem = '-'.join(['journey', str(loc.dccAddr), str(trak.nr), trak.dir()])
                self.debug("starting new journey: " + str(loc.dccAddr) + " heading " + trak.dir() + " on track " + str(trak.nr) + " classname: " + klassName + " mem: " + mem)
                self.startJourney(loc, klass, mem)


        # go through each track ...
        #for track in self.tracks:



    def handle(self):
        self.debug("Jack Starting")
        
        # turn layout power on
        self.powerState = powermanager.getPower()
        if self.powerState != jmri.PowerManager.ON:
            self.debug("turning power on")
            powermanager.setPower(jmri.PowerManager.ON)
            time.sleep(5)  # give the sensors time to wake up
        else:
            self.debug("power is on")

        # Initialise tracks
        self.initTracks()

        # Initialise locomotives and get their location.
        self.initLocos()

        # Main Loop
        loopcount = 0
        while True:
            loopcount += 1
            self.checkStatus() # see if we should be stopping
            if self.status == ESTOP:
                # Stop everything immediately
                self.eStop()
                print "Jack exits"
                return False
            self.checkJourneys()
            if self.status == STOPPING and len(self.memories) == 0:
                # We are doing a graceful stop and all journeys are done
                print "All done - exiting"
                return False
            self.startNewJourneys() # kick off new journeys, if appropriate
            if loopcount > 1
                self.debug('exiting')
                return False # stop the loop for the moment
            time.sleep(1)

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
