import jmri
import time
from myroutes import *
from jmri_bindings import *

# class StartUp :
#
#     def do(self) :
#
#         self.powerState = powermanager.getPower()
#         if self.powerState != jmri.PowerManager.ON :
#             powermanager.setPower(jmri.PowerManager.ON)
#             time.sleep(1)
#
#         r = None
#         tries = 0
#         while r == None and tries < 10 :
#             r = routes.getRoute('StartUp')
#             if r == None:
#                 tries += 1
#                 print "tries:", tries
#                 time.sleep(2)
#
#         r.activateRoute()
#         r.setRoute()
#         time.sleep(2)
#
#         r = routes.getRoute('Hertford Nth Inner')
#         r.activateRoute()
#         r.setRoute()
#         time.sleep(2)
#
#         r = routes.getRoute('Sth Sidings 1')
#         r.activateRoute()
#         r.setRoute()
#         time.sleep(2)
#
#         r = routes.getRoute('Back Passage')
#         r.activateRoute()
#         r.setRoute()
#         time.sleep(2)
#
#         r = routes.getRoute('Nth Siding 1')
#         r.activateRoute()
#         r.setRoute()
#
#
#         mem = memories.getMemory("North Link Lock")
#         if mem is not None:
#             mem.setValue(None)
#
#         mem = memories.getMemory("South Link Lock")
#         if mem is not None:
#             mem.setValue(None)
#
#         print "StartUp done."

lssensorlist = [112, 113, 114, 115, 116, 117, 105, 106, 107, 108, 109, 110, 101, 102, 103, 119, 120, 122, 123]
issensorlist = [18, 19, 20, 21, 22, 28, 29, 33, 34, 'IS32']
class SetStartupSensors:
    def __init__(self, lssensorlist, issensorlist):
        self.lssensorlist = lssensorlist
        self.issensorlist = issensorlist

    def do(self):
        for s in self.lssensorlist:
            name = 'LS' + str(s)
            sen = sensors.getSensor(name)
            sen.setKnownState(INACTIVE)
        for s in self.issensorlist:
            name = 'IS' + str(s)
            sen = sensors.getSensor(name)
            sen.setKnownState(INACTIVE)
        # clear display memories
        for i in range(1,7):
            m = memories.provideMemory("IMTRACK" + str(i) + "LOCO")
            m.setValue(None)
            m = memories.provideMemory("IMTRACK" + str(i) + "SPEED")
            m.setValue(None)


SetStartupSensors(lssensorlist, issensorlist).do()


#StartUp().do()
