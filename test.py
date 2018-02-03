import jmri
import java
from jmri_bindings import *

class Test(jmri.jmrit.automat.AbstractAutomaton):
    def handle(self):
        t = self.getThrottle(68, False)
        s = t.getSlot()
        print "slot", s.getSlot()
        print "id", s.id()
        print "status", s.getStatus()

Test().start()


