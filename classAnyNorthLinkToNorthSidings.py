import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
import lock
from jmri_bindings import *
from myroutes import *

class ClassAnyNorthLinkToNorthSidings(alex.Alex):

    def handle(self):
        self.loco.status = loco.ACTIVE
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        lok = lock.Lock()
        lok.getLock(NORTH, NORTHBOUND, self.loco)
        if lok.empty():
            raise RuntimeError("ruh roh - this should be impossible, did this loco release the lock when it stopped?")
        routes = self.requiredRoutes(siding)
        self.shortJourney(False, normalSpeed='fast', slowSpeed='fast', endBlock=siding, stopIRClear=IRSENSORS[siding.getId()], lock=lok, routes=routes)
        self.loco.status = SIDINGS
        self.loco.unselectSiding(siding)

class Class150NorthLinkToNorthSidings(ClassAnyNorthLinkToNorthSidings):
    pass