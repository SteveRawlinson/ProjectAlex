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

class Loco2144Shuttle(alex.Alex):
        

    def __init__(self):
        self.loco = 2144
        
    def handle(self):
            
        print "handling"
        start = time.time()
        
        loco = self.loco        
        self.knownLocation = None
        platformWaitTimeMsecs = self.platformWaitTimeMsecs

        # get a 'lock' on the north link track
        rc = self.getLock('North Link Lock', loco)
        if rc == False :
            return False 

        # Out the nth sidings to PAL P1
        routes = ['Hertford Nth Inner', 'Nth Siding 1']
        rc = self.shortJourney(self.t1, True, self.nthSiding1, self.palP1, 0.4, 0.2, 6000, routes = routes)
        if rc == False :
            return False         
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)
        self.unlock('North Link Lock', loco)
        
        # PAL to AAP
        rc = self.shortJourney(self.t1, True, self.palP1, self.aapP4, 0.4, 0.2, 5000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # AAP to FPK
        rc = self.shortJourney(self.t1, True, self.aapP4, self.fpkP1, 0.4, 0.25, 11000)
        if rc == False :
            return False
        print "waiting at platform for", platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs)

        # FPK to Sth Sidings
        rc = self.getLock('South Link Lock', loco)
        if rc == False :
            return False
        # set routes to sth sidings
        routes = ['Sth Sidings', 'Sth Hertford Inner']
        rc = self.shortJourney(self.t1, True, self.fpkP1, self.sthSidings, 0.4, 0.2, 0, self.sthSidingsClearIR, routes = routes)
        if rc == False :
            return False
        self.unlock('South Link Lock', loco)
        print "waiting in sidings for",  2 * platformWaitTimeMsecs / 1000, "secs"
        self.waitMsec(platformWaitTimeMsecs * 2)

        # out of sth sidings to FPK
        rc = self.getLock('South Link Lock', loco)
        if rc == False :
            return False
        # set routes to nth siding 1
        routes = ['Sth Hertford Outer', 'Sth Sidings'] 
        rc = self.shortJourney(self.t1, False, self.sthSidings, self.fpkP2, 0.4, 0.3, 3000, routes = routes)
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
        rc = self.getLock('North Link Lock', loco)
        if rc == False :
            return False
        # set routes
        routes = ['Nth Siding 1', 'Hertford Nth Outer']
        rc = self.shortJourney(self.t1, False, self.palP2, self.nthSiding1, 0.4, 0.1, 0, self.nthSiding1ClearIR, routes = routes)
        if rc == False :
            return False
        
        print "route complete."
        self.unlock('North Link Lock')
        
        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False
        
        
		

		
Loco2144Shuttle().start()
