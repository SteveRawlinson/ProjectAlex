import jmri
from jmri_bindings import *
from myroutes import *
import re
import track
import datetime

# This is a mixin
class Util:

    def debug(self, message):
        if DEBUG:
            if hasattr(self, 'loco') and self.loco is not None:
                print str(datetime.datetime.now()) + ' ' + str(self.loco.dccAddr) + ': ' + message
            elif hasattr(self, 'dccAddr'):
                print str(datetime.datetime.now()) + ' ' + str(self.dccAddr) + ': ' + message
            else:
                print str(datetime.datetime.now()) + ': ' + message

    def log(self, message="", filename="jmri.log"):
        file=open('C:\Users\steve\\' + filename, 'a')
        if hasattr(self, 'loco'):
            logstr = str(datetime.datetime.now()) + ' ' + str(self.loco.dccAddr) + ': ' + message
        elif hasattr(self, 'dccAddr'):
            logstr = str(datetime.datetime.now()) + ' ' + str(self.dccAddr) + ': ' + message
        else:
            logstr = str(datetime.datetime.now()) + ': ' + message
        file.write(logstr + '\r\n')
        file.close()

    # Returns True if the block indicated by +thing+ is occupied. The +thing+
    # can be a string, a layoutblock, or a block.
    def isBlockOccupied(self, thing):
        block, sensor = self.convertToLayoutBlockAndSensor(thing)
        #self.debug("  block: " + block.getDisplayName())
#        if sensor is not None:
#            self.debug("  sensor: " + sensor.getSystemName())
        if sensor is None:
#            self.debug("  sensor is none")
            return False
        if sensor.getKnownState() == ACTIVE:
            # see if we know the identity of the loco
            b = block.getBlock()
            if b.getValue() is not None and b.getValue() != '':
 #               self.debug("  returning value: " + b.getValue())
                return b.getValue()
            else:
                return True
        else:
            return False

    # Returns True if the block referred to be +thing+ (which can be
    # a string, a block, or a layoutBlock) is on the visible part of
    # the layout
    def isBlockVisible(self, thing):
        if type(thing) != str and type(thing) != unicode:
            block, sensor = self.convertToLayoutBlockAndSensor(thing)
            blockname = block.getId()
        else:
            blockname = thing
        if re.match('^(FPK|PAL|NSG|AAP)', blockname):
            return True
        return False

    # Initialises the tracks[] array, according to information in the myroutes.py file
    def initTracks(self):
        for t in TRACKS:
            tr = track.Track(len(self.tracks) + 1, t[0], t[1], t[2], t[3], t[4])
            self.tracks.append(tr)
            #print "New track: array index: " + str(self.tracks.index(tr)) + " track nr: " + str(tr.nr) + " stops: " + str(tr.stops) + " fast: " + str(tr.fast)


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

    def getJackStatus(self):
        mem = memories.provideMemory('IMJACKSTATUS')
        v = mem.getValue()
        return int(v)

    def sidingMemoryName(self, siding):
        if type(siding) == str:
            return "IMSIDING" + siding.upper()
        elif type(siding) == jmri.Block:
            return"IMSIDING" + siding.getUserName().upper()
        else:
            # layoutblock
            return "IMSIDING" + siding.getId().upper()

    def freeSidingCount(self, sidings):
        count = 0
        for s in sidings:
            b = blocks.getBlock(s)
            if b.getState() != OCCUPIED:
                count += 1
        return count





