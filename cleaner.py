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
            print "New track: array index: " + str(self.tracks.index(tr)) + " track nr: " + str(tr.nr) + " stops: " + str(tr.stops) + " fast: " + str(tr.fast)

    # Cleans a pair of tracks, eg. tracks 1 and 2
    def trackPair(self):

        startBlock = self.loco.block
        self.loco.status = loco.MOVING

        # we will shortly start moving but we don't know which
        # direction we're facing. Get the next sensor in
        # each direction
        trak = track.Track.findTrackByBlock(self.tracks, self.loco.block)
        self.debug("track: " + str(trak.nr))
        if trak.northbound():
            direction = 'Northbound'
        else:
            direction = 'Southbound'
        self.debug("direction: " + direction)
        nextLayoutBlockNorth = layoutblocks.getLayoutBlock(trak.nextBlockNorth(self.loco.block).getUserName())
        nextSensorNorth = nextLayoutBlockNorth.getOccupancySensor()
        nextLayoutBlockSouth = layoutblocks.getLayoutBlock(trak.nextBlockSouth(self.loco.block).getUserName())
        nextSensorSouth = nextLayoutBlockSouth.getOccupancySensor()

        # check those sensors are not active
        if nextSensorNorth.knownState == ACTIVE:
            print "Next block north (" + nextLayoutBlockNorth.getUserName() + ") is occupied - quitting"
            return False
        if nextSensorSouth.knownState == ACTIVE:
            print "Next block south (" + nextLayoutBlockSouth.getUserName() + ") is occupied - quitting"
            return False

        # check the reverse loops are empty
        if blocks.getBlock(NORTH_REVERSE_LOOP).getState() == OCCUPIED:
            print "block", NORTH_REVERSE_LOOP, "occupied, quitting"
        if blocks.getBlock(SOUTH_REVERSE_LOOP).getState() == OCCUPIED:
            print "block", SOUTH_REVERSE_LOOP, "occupied, quitting"

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
        self.debug("waiting for either " + nextLayoutBlockNorth.getUserName() + " or " + nextLayoutBlockSouth.getUserName() +" to go active")
        sensorList = [nextSensorNorth, nextSensorSouth]
        self.changedSensors(sensorList) # set the initial states
        self.waitChange(sensorList, 60 * 1000)
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
            self.debug("track " + str(trak.nr) + " is northbound but changedSensor is nextSensorSouth: " + nextSensorSouth.getDisplayName())
            wrongWay = True
        if trak.southbound() and changedSensor == nextSensorNorth:
            self.debug("track " + str(trak.nr) + " is southbound but changedSensor is nextSensorNorth: " + nextSensorNorth.getDisplayName())
            wrongWay = True
        if wrongWay is True:
            self.debug("going the wrong way")
            self.loco.reverse()


        # we are now moving in thr right direction, keep going until
        # we get to the north/south link

        if trak.northbound():
            lb = layoutblocks.getLayoutBlock('North Link')
            ls = lb.getOccupancySensor()
        else:
            lb = layoutblocks.getLayoutBlock('South Link')
            ls = lb.getOccupancySensor()

        if ls.knownState == INACTIVE:
            self.waitChange([ls], 60 * 1000)

        # we are at the link
        self.debug("link reached")
        self.loco.setBlock(lb)

        # go through the reversing loop
        if trak.northbound():
            loop = NORTH_REVERSE_LOOP
        else:
            loop = SOUTH_REVERSE_LOOP
        self.reverseLoop(loop, stop=False)

        # work out which trak we are going down now
        if trak.southbound():
            trak = self.tracks[trak.nr ] # move up one (eg. track 1 -> 2)
        else:
            trak = self.tracks[trak.nr - 2] # move up one (eg. 2 -> 1)

        # set routes for entry and exit
        rt = trak.entryRoute()
        self.setRoute(rt)
        rt = trak.exitRoute()
        self.setRoute(rt)

        # wait till we get to the link
        if trak.northbound():
            lb = layoutblocks.getLayoutBlock('North Link')
            ls = lb.getOccupancySensor()
        else:
            lb = layoutblocks.getLayoutBlock('South Link')
            ls = lb.getOccupancySensor()

        if ls.knownState == INACTIVE:
            self.waitChange([ls], 60 * 1000)

        # we are at the link
        self.loco.setBlock(lb)

        # go through the reversing loop
        if trak.northbound():
            loop = NORTH_REVERSE_LOOP
        else:
            loop = SOUTH_REVERSE_LOOP
        self.reverseLoop(loop, stop=False)

        # work out which track we are going (back) down now
        if trak.southbound():
            trak = self.tracks[trak.nr] # move up one (eg. track 1 -> 2)
        else:
            trak = self.tracks[trak.nr - 2] # move up one (eg. 2 -> 1)

        # set route for entry
        rt = trak.entryRoute()
        self.setRoute(rt)
        # set route for exit in case coming off the last block overruns the track
        rt = trak.exitRoute()
        self.setRoute(rt)

        # wait for the original block to go active
        s = startBlock.getSensor()
        if s.knownState != ACTIVE:
            self.waitChange([s])
        self.waitChange([s])
        self.loco.setSpeedSetting(-1)

    def northSidings(self):
        trak = track.Track.findTrackByBlock(self.tracks, self.loco.block)
        self.debug("track: " + str(trak.nr))

        startBlock = self.loco.block()

        # set exit route for this track
        route = trak.exitRoute()
        self.setRoute(route)

        for siding in NORTH_SIDINGS:
            # set the route into the siding
            route = self.requiredRoutes(siding)
            self.setRoute(route)
            self.loco.forward()
            self.loco.setSpeedSetting(0.4)
            # wait for the siding to become occupied
            lb = layoutblocks.getLayoutBlock(siding)
            ls = lb.getOccupancySensor()
            if ls.knownState() == ACTIVE:
                raise RuntimeError("block " + siding + " is occupied")
            else:
                self.waitChange([ls], 60 * 1000)
            # wait for a bit to get into the siding
            time.sleep(CLEANER_SIDING_TIME[siding])
            # turn loco around
            self.loco.reverse()
            # wait till IR sensor goes active
            ls = sensors.getSensors(IRSENSORS["North Link Clear"])
            if ls.knownState() == INACTIVE:
                self.waitChange([ls], 60 * 1000)
            # and then wait for it to clear
            self.waitChange([ls], 60 * 1000)
            self.loco.setSpeedSetting(0)

        # reverse back to the block we started on
        self.loco.reverse()
        self.loco.setSpeedSetting(0.4)
        sen = startBlock.getOccupancySensor()
        self.waitChange([sen], 120 * 1000)
        # and just past it
        self.loco.setSpeedSetting(0.3)
        self.waitChange([sen], 60 * 1000)
        self.looo.setSpeedSetting(0)



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
        self.debug("got throttle")

        if poweredOn:
            # stop the loco in case it started up
            self.loco.emergencyStop()
            self.debug("sleeping for 5 ...")
            time.sleep(5)

        # get a block if we don't have one
        self.debug("sorting out blocks")
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


        self.trackPair()

        self.debug("exiting")
        return False


loc = loco.Loco(7405)
Cleaner(loc).start()