import jmri
import time


class MyTest(jmri.jmrit.automat.AbstractAutomaton):

    def init(self):
        self.t = self.getThrottle(2144, True)

    def handle:
        print "speed 0.2"
        self.t.setSpeed(0.2)
        time.sleep(3)
        print "speed -1"
        self.t.setSpeed(-1)
        time.sleep(3)
        print "speed 0"
        self.t.setSpeed(0)

MyTest().start()