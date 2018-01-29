import sys
import jmri
from jmri_bindings import *
from myroutes import *
import re
import track
import datetime
import random

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
            self.log('[debug]: ' + message)

    def log(self, message="", filename=None):
        if filename is None:
            filename = LOGFILE
        file=open(filename, 'a')
        if hasattr(self, 'loco'):
            logstr = str(datetime.datetime.now()) + ' ' + str(self.loco.dccAddr) + ': ' + message
        elif hasattr(self, 'dccAddr'):
            logstr = str(datetime.datetime.now()) + ' ' + str(self.dccAddr) + ': ' + message
        else:
            logstr = str(datetime.datetime.now()) + ': ' + message
        file.write(logstr + '\n')
        file.close()

    @classmethod
    def clog(cls, message="", filename=None, loc=None, dccAddr=None):
        if filename is None:
            filename = LOGFILE
        file=open(filename, 'a')
        if loc:
            logstr = str(datetime.datetime.now()) + ' ' + str(loc.dccAddr) + ': ' + message
        elif dccAddr:
            logstr = str(datetime.datetime.now()) + ' ' + str(dccAddr) + ': ' + message
        else:
            logstr = str(datetime.datetime.now()) + ': ' + message
        file.write(logstr + '\n')
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

    # Returns the contents of the 'thing'
    def getBlockContents(self, thing):
        layoutblock, sensor = self.convertToLayoutBlockAndSensor(thing)
        block = layoutblock.getBlock()
        return block.getValue()

    # Returns True if the block referred to be +thing+ (which can be
    # a string, a block, or a layoutBlock) is on the visible part of
    # the layout
    def isBlockVisible(self, thing):
        if thing is None:
            return False
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
            self.debug("geting sensor " + TRACKSENSORS[tr.nr])
            s = sensors.getSensor(TRACKSENSORS[tr.nr])
            if tr.us:
                s.setKnownState(INACTIVE)
            else:
                s.setKnownState(ACTIVE)
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

    # Get the name for the memory associated with this siding
    def sidingMemoryName(self, siding):
        if type(siding) == str:
            return "IMSIDING" + siding.upper()
        elif type(siding) == jmri.Block:
            return"IMSIDING" + siding.getUserName().upper()
        else:
            # layoutblock
            return "IMSIDING" + siding.getId().upper()

    # Returns the number of sidings that are unoccupied
    def freeSidingCount(self, sidings):
        count = 0
        for s in sidings:
            b = blocks.getBlock(s)
            if b.getState() != OCCUPIED:
                count += 1
        return count

    # Returns the number of locos from the list supplied which are
    # currently in the sidings supplied
    def locoCountInSidings(self, locos, sidings):
        count = 0
        for l in locos:
            if l.block.getUserName() in sidings:
                count += 1
        return count

    # Accepts a list of elements each of which is a list of
    # two elements. The zeroeth element is the things we are
    # chooseing between and the first element is the weight.
    # Returns the zeroeth element of the chosen item from the
    # list.
    @classmethod
    def weighted_choice(cls, list):
        tot = 0.0
        for e in list:
            tot += e[1]
        n = random.random() * tot
        cls.clog("tot: " + str(tot) + " random number: " + str(n))
        for e in list:
            n -= e[1]
            cls.clog("deducting " + e[0].name() + " weight: " + str(e[1]))
            if n <= 0.0:
                cls.clog(e[0].name() + " wins")
                return e[0]
            cls.clog(str(n) + " remaining")





