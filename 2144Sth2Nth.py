import jarray
import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex

alex.sensors = sensors # explicitly add to auto namespace
alex.memories = memories
alex.routes = routes
alex.layoutblocks = layoutblocks
alex.ACTIVE = ACTIVE

class Loco2144Sth2Nth(alex.Alex):
        

    def __init__(self):
        self.loco = 2144
        
    def handle(self):
            
        print "handling"
        start = time.time()
        
        loco = self.loco        
        self.knownLocation = None
        platformWaitTimeMsecs = self.platformWaitTimeMsecs

        # out of sth sidings to FPK
        lock = self.getLock('South Link Lock', loco)
        if lock == False :
            return False

        # set routes to nth siding 1
        routes = ['Sth Hertford Outer', 'Sth Sidings'] 
        rc = self.shortJourney(self.t1, False, self.sthSidings, self.fpkP2, 0.4, 0.3, 3000, routes = routes, lock = lock)
        if rc == False :
            return False
        self.unlock('South Link Lock', loco)
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to AAP
        rc = self.shortJourney(self.t1, False, self.fpkP2, self.aapP3, 0.4, 0.2, 2000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 3000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        
        # AAP to PAL
        rc = self.shortJourney(self.t1, False, self.aapP3, self.palP2, 0.4, 0.3, 1000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # PAL to nth siding 1
        lock = self.getLock('North Link Lock', loco)
        if lock == False :
            return False
        # set routes
        routes = ['Nth Siding 1', 'Hertford Nth Outer']
        rc = self.shortJourney(self.t1, False, self.palP2, self.nthSiding1, 0.4, 0.1, 0, self.nthSiding1ClearIR, routes = routes, lock = lock)
        if rc == False :
            return False
        
        print "route complete."
        self.unlock('North Link Lock')
        
        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False
        
        
		

		
Loco2144Sth2Nth().start()
