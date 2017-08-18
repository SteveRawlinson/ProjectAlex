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
from loco2144Nth2SthTrack1 import *
from loco2144Sth2NthTrack2 import *


# DCC_ADDRESSES = [68, 5144, 2144, 6022, 3213, 1087]
DCC_ADDRESSES = [2144, 5144]
DEBUG = True


class Jack:
    
    def __init__(self):
        self.locos = [] # array of Loco
        self.tracks = [0,0,0,0,0,0] # keeping  track of tracks
        self.memories = [] # list of names of  active journeys

    def debug(self, message):
        if DEBUG:
            print "Jack:", message

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
                    if blk.getState() == OCCUPIED and blk.getValue() is None:
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

    # Returns True if the loco supplied is in the north sidings
    def northSidings(self, loc):
        return loc.northSidings

    # Returns True is hte loco supplied in south sidings
    def southSidings(self, loc):
        return loc.southSidings

    def locosSouth(self):
        southList = []
        for l in self.locos:
            if self.southSidings(l):
                southList.append(l)
        return southList

    def startJourney(self, loco, klass, mem):
        mem = memories.provideMemory(mem)
        mem.setValue(1)
        klass(loco).start()

    def start(self):
        self.debug("Jack Starting")
        
        # turn layout power on
        self.powerState = powermanager.getPower()
        if self.powerState != jmri.PowerManager.ON:
            self.debug("turning power on")
            powermanager.setPower(jmri.PowerManager.ON)
            time.sleep(5)  # give the sensors time to wake up
        else:
            self.debug("power is on")

        # Initialise locomotives and get their location.
        self.initLocos()

        klassName = "Loco2144Sth2NthTrack2"
        #klassName = "Loco2144Nth2SthTrack1"
        constructor = globals()[klassName]
        self.startJourney(self.locos[0], constructor, mem)

        time.sleep(5)
        print "Jack continues"
        print "loco", self.locos[0].dccAddr, "status is", self.locos[0].status
        print "Jack exits"

Jack().start()
