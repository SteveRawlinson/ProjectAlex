import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

# alex.sensors = sensors  # explicitly add to auto namespace
# alex.memories = memories
# alex.routes = routes
# alex.layoutblocks = layoutblocks
# alex.ACTIVE = ACTIVE


class Cleaner(alex.Alex):

    def __init__(self, loc):
        self.loco = loc




    def handle(self):

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
            time.sleep(5)

        # get a block if we don't have one
        if self.loco.block is None:
            # put up a dropbox for the user to select the block
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
        trak = track.Track.findTrackByBlock(self.loco.block)
        nextSensorNorth = layoutblocks.getLayoutBlock(trak.nextBlockNorth(self.loco.block).getUserName())
        nextSensorSouth = layoutblocks.getLayoutBlock(trak.nextBlockSouth(self.loco.block).getUserName())

        # check those sensors are not active
        if nextSensorNorth.knownState == ACTIVE:
            print "Next block north is occupied - quitting"
            return False
        if nextSensorSouth.knownState == ACTIVE:
            print "Next block south is occupied - quitting"
            return False

        # set the direction to forward
        self.loco.forward()

        # set the speed
        self.loco.setSpeedSetting(0.4)

        # check which sensor comes up
        sensorList = [nextSensorNorth, nextSensorSouth]
        self.changedSensors(sensorList) # set the initial states
        self.waitChange(sensorList, 30 * 1000)
        changedList = self.changedSensors(sensorList)
        if len(changedList) == 0:
            puts "Timed out waiting for a sensor to come active - quitting"
            self.loco.emergencyStop()
            return False
        if len(changedList) < 1:
            puts "both north and south sensors changed, this is surely unpossible - quitting"
            self.loco.emergencyStop()
            return False
        changedSensor = changedList[0]
        if trak.northbound() and changedSensor == nextSensorSouth:
            self.loco.idle()
            self.




loc = loco.Loco(7405)
Cleaner(loc, mem).start()