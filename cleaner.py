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

        if not self.loco.northSidings():
            print str(self.loco.dccAddr) + ": not in north sidings. Block: " + self.loco.block.getUserName()
            raise RuntimeError(str(self.loco.dccAddr) + ": I'm not in the north sidings!")

        self.loco.status = loco.MOVING





loc = loco.Loco(7405)
Cleaner(loc, mem).start()