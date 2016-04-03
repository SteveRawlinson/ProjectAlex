import jarray
import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco

class Loco5144Nth2Sth(alex.Alex):

    def __init__(self, loco):
        self.loco = loco
        self.knownLocation = None

    def handle(self):
            
        start = time.time()
        
        platformWaitTimeMsecs = 5000
        self.knownLocation = None

        # out of nth sidings to NSG
        rc = self.getLock('IMNTHLINK')
        if rc == False :
            return False
        # set routes
        routes = self.requiredRoutes(self.loco.block) + self.requiredRoutes("PAL P1")
        rc = self.shortJourney(True, self.nthSiding1, self.nsgP1, 0.4, 0.3, 7000, routes=routes)
        if rc == False :
            return False
        self.unlock('IMNTHLINK', self.loco.dccAddr)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        return None

        # NSG to AAP
        rc = self.shortJourney(True, self.nsgP1, self.aapP2, 0.4, 0.2, 4000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 3000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        
        # AAP to FPK
        rc = self.shortJourney(True, self.aapP2, self.fpkP3, 0.4, 0.3, 7000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to sth sidings
        rc = self.getLock('IMSTHLINK', self.loco.dccAddr)
        if rc == False :
            return False
        # set routes
        self.setMyRoute('Sth Sidings')
        self.setMyRoute('Sth Welwyn Inner')
        rc = self.shortJourney(True, self.fpkP3, self.sthSidings, 0.3, 0.1, 0, self.sthSidingsClearIR)
        if rc == False :
            return False
        print "waiting in sidings for",  2 * platformWaitTimeMsecs / 1000, "secs"
        print "route complete."
        self.unlock('IMSTHLINK')
        
        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False

l = loco.Loco(5144)
l.initBlock()
Loco5144Nth2Sth(l).start()

