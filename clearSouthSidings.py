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

class ClearSouthSidings(alex.Alex):

    def __init__(self):
        self.locos =[]
        self.tracks = []
        self.loco = None
        self.sensorStates = None

    def go(self):
        self.clearSidings(SOUTH)


ClearSouthSidings().start()

