import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
import track
from jmri_bindings import *
from javax.swing import JOptionPane
from myroutes import *

DEBUG = True


class Cleaner(alex.Alex):

    def __init__(self, loc):
        self.loco = loc
        self.tracks = []


    def debug(self, message):
        if DEBUG:
            print 'cleaner: ' + message

    # Initialises the tracks[] array, according to information in the myroutes.py file
    def initTracks(self):
        for t in TRACKS:
            tr = track.Track(len(self.tracks) + 1, t[0], t[1], t[2], t[3])
            self.tracks.append(tr)
            print "New track: " + str(tr.nr) + " stops: " + str(tr.stops) + " fast: " + str(tr.fast)

    def handle(self):

        # get track info
        self.initTracks()

        # turn layout power on
        self.powerState = powermanager.getPower()
        if self.powerState != jmri.PowerManager.ON:
            poweredOn = True
            self.debug("turning power on")
            powermanager.setPower(jmri.PowerManager.ON)
        else:
            poweredOn = False
            self.debug("power is on")

        # get a throttle
        self.getLocoThrottle(self.loco)

        # stop the loco in case we've just turned power on and it started up
        self.loco.emergencyStop()

        if poweredOn:
            self.debug("sleeping for 5 ...")
            time.sleep(5)

        # get a block if we don't have one
        if self.loco.block is None:
            # put up a dropbox for the user to select the block
            blist = ['not in use']
            blockNameList = []
            for t in self.tracks:
                blockNameList += t.blocks
            for blockName in blockNameList:
                blk = blocks.getBlock(blockName)
                if blk.getState () == OCCUPIED:
                    if str(blk.getValue()) == str(self.loco.dccAddr):
                        self.debug("found loco in block " + blockName)
                        self.loco.setBlock(blk)
                    elif blk.getValue() is None or blk.getValue() == "":
                        blist.append(blockName)
            if self.loco.block is None:
                self.debug("getting block from user")
                b = JOptionPane.showInputDialog(None,
                                            "Select starting block for " + self.loco.name(),
                                            "Choose block",
                                            JOptionPane.QUESTION_MESSAGE,
                                            None,
                                            blist,
                                            'not in use')
                if b is None:
                    # User cancelled
                    return False
                if b != "not in use":
                    # set the block and add the new loco to the list
                    self.loco.setBlock(b)

        if self.loco.block is None:
            raise RuntimeError("I don't have a block!")

        self.loco.status = loco.MOVING

        # we will shortly start moving but we don't know which
        # direction we're facing. Get the next sensor in
        # each direction
        trak = track.Track.findTrackByBlock(self.tracks, self.loco.block)
        nextLayoutBlockNorth = layoutblocks.getLayoutBlock(trak.nextBlockNorth(self.loco.block).getUserName())
        nextSensorNorth = nextLayoutBlockNorth.getOccupancySensor()
        nextLayoutBlockSouth = layoutblocks.getLayoutBlock(trak.nextBlockSouth(self.loco.block).getUserName())
        nextSensorSouth = nextLayoutBlockSouth.getOccupancySensor()

        # check those sensors are not active
        if nextSensorNorth.knownState == ACTIVE:
            print "Next block north is occupied - quitting"
            return False
        if nextSensorSouth.knownState == ACTIVE:
            print "Next block south is occupied - quitting"
            return False

        # set the direction to forward
        self.loco.forward()

        # set exit routes in both directions in case we're facing the wrong way
        route = trak.exitRoute()
        self.setRoute(route)
        route = trak.exitRoute(reverse = True)
        self.setRoute(route)

        # set the speed
        self.loco.setSpeedSetting(0.4)

        # check which sensor comes up
        sensorList = [nextSensorNorth, nextSensorSouth]
        self.changedSensors(sensorList) # set the initial states
        self.waitChange(sensorList, 30 * 1000)
        changedList = self.changedSensors(sensorList)
        if len(changedList) == 0:
            print "Timed out waiting for a sensor to come active - quitting"
            self.loco.emergencyStop()
            return False
        if len(changedList) > 1:
            print "both north and south sensors changed, this is surely unpossible - quitting"
            self.loco.emergencyStop()
            return False
        changedSensor = changedList[0]
        wrongWay = False
        if trak.northbound() and changedSensor == nextSensorSouth:
            wrongWay = True
        if trak.southbound() and changedSensor == nextSensorNorth:
            wrongWay = True
        if wrongWay is True:
            self.loco.setSpeedSetting(0)
            self.debug("going the wrong way")
            self.loco.reverse()
            self.loco.setSpeedSetting(0.4)

        # we are now moving in thr right direction, keep going until
        # we get to the north/south link

        if trak.northbound():
            lb = layoutblocks.getLayoutBlock('North Link')
            ls = lb.getOccupanySensor
        else:
            lb = layoutblocks.getLayoutBlock('South Link')
            ls = lb.getOccupanySensor

        if ls.knownState == INACTIVE:
            self.waitChange([ls], 60 * 1000)

        # we are at the link
        self.debug("link reached")



loc = loco.Loco(7405)
Cleaner(loc).start()