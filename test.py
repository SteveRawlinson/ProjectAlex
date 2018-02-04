import jmri
import java
from jmri_bindings import *
from myroutes import *

class Test(jmri.jmrit.automat.AbstractAutomaton):
    def handle(self):
        t = self.getThrottle(68, False)
        s = t.getLocoNetSlot()
        print "slot", s.getSlot()
        print "id", s.id()
        print "status", s.slotStatus()
        for k in LN_SLOT_STATUS:
            print str(k), 'correspond to', str(LN_SLOT_STATUS[k])
        print 'in-use', LOCO_IN_USE
        print 'free', LOCO_FREE
        print 'idle', LOCO_IDLE
        print 'common', LOCO_COMMON

Test().start()


