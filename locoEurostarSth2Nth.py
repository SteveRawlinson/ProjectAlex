import jarray
import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex

alex.sensors = sensors # explicitly add to namespace
alex.memories = memories
alex.routes = routes
alex.layoutblocks = layoutblocks
alex.ACTIVE = ACTIVE

class LocoEurostarSth2Nth(alex.Alex):
        

    def __init__(self):
        self.loco = 3213
        
    def handle(self):
            
        start = time.time()
        
        loco = self.loco        
        self.knownLocation = None
        platformWaitTimeMsecs = self.platformWaitTimeMsecs

        # get a 'lock' on the link track
        lock = self.getLock('South Link Lock', loco)
        if lock == False :
            return False 

#  shortJourney(self, throttle, direction, startBlock, endBlock, normalSpeed, slowSpeed, slowTime = 0, stopIRClear = None, checkSensor = None, routes = []):


        # Out the sth sidings to FPK
        routes = ['Back Passage', 'Sth Fast Outer']
        rc = self.shortJourney(self.t1, False, "Back Passage", "FPK P8", 0.2, -1, 0, routes = routes, lock = lock)
        if rc == False :
            self.t1.setSpeedSetting(0)
            return False         
        lock = None

        # open the throttle and off to Nth Fast Outer 1
        print "calling"
        rc = self.shortJourney(self.t1, False, "FPK P8", "Nth Fast Outer 1", 0.4, -1, 0)
        if rc == False :
            self.t1.setSpeedSetting(0)
            return False
        
        # get a lock on the north link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('North Link Lock', loco)
        if lock == False:
            # stop the train
            self.gradualHalt(self.t1, 2)
            # wait for a lock
            lock = self.getLock('North Link Lock')
            if lock == False :
                return False
        else :
            # we got a lock
            self.waitMsec(500)
            # check we still have it
            rc = self.checkLock(lock, loco)
            if rc == False :
                # we lost it, abort!
                self.t1.setSpeedSetting(0)
                print loco, "race conditions on South Link Lock?"
                return False

        # into the sidings
        routes = ['Nth Fast Outer', 'Nth Siding 2']
        rc = self.shortJourney(self.t1, False, 'Nth Fast Outer 1', 'Nth Sidings 2', 0.2, 0.1, 0, self.nthSiding2ClearIR, routes = routes, lock = lock)
        

        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False
        
        
		

LocoEurostarSth2Nth().start()
