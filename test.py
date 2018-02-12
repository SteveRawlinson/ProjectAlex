import jmri
import java
from jmri_bindings import *
import time

class Test(jmri.jmrit.automat.AbstractAutomaton):
    def handle(self):
        print 'boo'
        # list = jmri.jmrit.roster.Roster.instance().getEntriesByDccAddress('68')
        # re = list[0]
        # print re.getDccAddress()
        t = self.getThrottle(2128, True)
        re = t.getRosterEntry()
        print re
        s = t.getLocoNetSlot()
        print "slot", s.getSlot()
        print "id", s.id()
        print "status", s.slotStatus()
        time.sleep(1)
        t2 = self.getThrottle(2128, True)
        print "t == t2: ", t == t2
        t.setSpeedSetting(0.2)
        time.sleep(3)
        t2.setSpeedSetting(0)
        time.sleep(2)
        self.releaseThrottle(t)
        print 'done'

Test().start()


