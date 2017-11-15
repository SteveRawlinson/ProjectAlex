import jmri
from jmri_bindings import *
from myroutes import *

# This is a mixin
class Util:

    def __init__(self):
        pass

    def debug(self, message):
        if DEBUG:
            print message

    # Returns True if the block indicated by +thing+ is occupied. The +thing+
    # can be a string, a layoutblock, or a block.
    def isBlockOccupied(self, thing):
        self.debug("isBlockOccupied: thing type: " + type(thing).__name__ + " value: " + str(thing))
        block, sensor = self.convertToLayoutBlockAndSensor(thing)
        self.debug("  block: " + block.getDisplayName())
        if sensor is not None:
            self.debug("  sensor: " + sensor.getSystemName())
        if sensor is None:
            self.debug("  sensor is none")
            return False
        if sensor.getKnownState() == ACTIVE:
            # see if we know the identity of the loco
            b = block.getBlock()
            if b.getValue() is not None:
                self.debug("  returning value: " + b.getValue())
                return b.getValue()
            else:
                return True
        else:
            return False



