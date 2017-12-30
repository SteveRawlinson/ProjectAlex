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
        if self.block.getUserName() != 'North Link':
            raise RuntimeError("I'm not on the North Link!")
        siding = self.loco.selectSiding(NORTH_SIDINGS)
        lok = lock.Lock()
        lok.getLock(NORTH, NORTHBOUND, self.loco)
        if lok.empty():
            raise RuntimeError("ruh roh")
        routes = self.requiredRoutes(siding)
        self.shortJourney(False, normalSpeed='fast', slowSpeed='fast', endBlock=siding, stopIRClear=IRSENSORS[siding.getId()], lock=lok, routes=routes)

class Class150NorthLinkToNorthSidings(ClassAnyNorthLinkToNorthSidings):
    pass