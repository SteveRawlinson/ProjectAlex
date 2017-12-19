import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class ClassAnyNorthLinkToNorthSidings(alex.Alex):

    def handle(self):
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        self.shortJourney(False, endBlock=siding, endIRSensor=IRSENSORS[siding])

class Class150NorthLinkToNorthSidinga(ClassAnyNorthLinkToNorthSidings):
    pass