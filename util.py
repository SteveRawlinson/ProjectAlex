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


    # Determine what 'thing' is (string name of a block, the block itself, or the sensor of the block)
    # and return the layout block and the sensor (if there is one).
    def convertToLayoutBlockAndSensor(self, thing):
        #self.debug("thing type: " + str(type(thing).__name__))
        if type(thing) == str or type(thing) == unicode:
            lb = layoutblocks.getLayoutBlock(thing)
            if lb is None:
                raise RuntimeError("no such block: " + thing)
            block = lb
            sensor = lb.getOccupancySensor()
        elif type(thing) == jmri.jmrit.display.layoutEditor.LayoutBlock:
            # startBlock is a LayoutBlock
            block = thing
            sensor = thing.getOccupancySensor()
        elif type(thing) == jmri.Block:
            # thing is a Block
            lb = layoutblocks.getLayoutBlock(thing.getUserName())
            if lb is None:
                raise RuntimeError("no such layoutBlock: " + thing.getUserName())
            block = lb
            sensor = block.getOccupancySensor()
        else:
            # thing is the sensor
            sensor = thing
            block = layoutblocks.getBlockWithSensorAssigned(thing)
        return block, sensor

