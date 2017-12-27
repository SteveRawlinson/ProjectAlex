import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
import lock
from jmri_bindings import *
from myroutes import *

DEBUG = True

class Mytest(alex.Alex):

    def __init__(self):
        self.tracks = []

    def do(self):
        self.initTracks()
        t = self.tracks[1]
        blk = blocks.getBlock("PAL P2")
        b = t.nextBlockNorth(blk)
        print type(b).__name__
        print b.getUserName()


Mytest().do()

