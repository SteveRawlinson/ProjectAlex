import jarray
import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex

alex.sensors = sensors # explicitly add to  namespace
alex.memories = memories
alex.routes = routes
alex.layoutblocks = layoutblocks
alex.ACTIVE = ACTIVE

class Loco5144Nth2Sth(alex.Alex):
        
    def __init__(self):
        self.loco = 5144
    
    def handle(self):
            
        start = time.time()
        
        platformWaitTimeMsecs = 5000
        loco = self.loco        
        self.knownLocation = None

        # out of nth sidings to NSG
        rc = self.getLock('IMNTHLINK', loco)
        if rc == False :
            return False
        # set routes to nth siding 1
        self.setMyRoute('Welwyn Inner')
        self.setMyRoute('Nth Siding 1')
        rc = self.shortJourney(self.t1, True, self.nthSiding1, self.nsgP1, 0.4, 0.3, 7000)
        if rc == False :
            return False
        self.unlock('IMNTHLINK', loco)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # NSG to AAP
        rc = self.shortJourney(self.t1, True, self.nsgP1, self.aapP2, 0.4, 0.2, 4000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 3000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        
        # AAP to FPK
        rc = self.shortJourney(self.t1, True, self.aapP2, self.fpkP3, 0.4, 0.3, 7000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to sth sidings
        rc = self.getLock('IMSTHLINK', loco)
        if rc == False :
            return False
        # set routes
        self.setMyRoute('Sth Sidings')
        self.setMyRoute('Sth Welwyn Inner')
        rc = self.shortJourney(self.t1, True, self.fpkP3, self.sthSidings, 0.3, 0.1, 0, self.sthSidingsClearIR)
        if rc == False :
            return False
        print "waiting in sidings for",  2 * platformWaitTimeMsecs / 1000, "secs"
        print "route complete."
        self.unlock('IMSTHLINK')
        
        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False
        
        
		

		
Loco5144Nth2Sth().start()
