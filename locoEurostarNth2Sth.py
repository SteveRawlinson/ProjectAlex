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
        lock = self.getLock('North Link Lock', loco)
        if lock == False :
            return False 

#  shortJourney(self, throttle, direction, startBlock, endBlock, normalSpeed, slowSpeed, slowTime = 0, stopIRClear = None, checkSensor = None, routes = []):


        # Out the Nth sidings to Nth Fast Inner 1
        routes = ['Nth Fast Inner', 'Nth Siding 2']
        rc = self.shortJourney(self.t1, True, "Nth Sidings 2", "Nth Fast Inner 1", 0.2, -1, 0, routes = routes, lock = lock)
        if rc == False :
            self.t1.setSpeedSetting(0)
            return False         
        lock = None

        # open the throttle and off to FPK P7
        rc = self.shortJourney(self.t1, True, "Nth Fast Inner 1", "FPK P7", 0.4, -1, 0)
        if rc == False :
            self.t1.setSpeedSetting(0)
            return False
        
        # slow down a bit
        self.t1.setSpeedSetting(0.2)

        # get a lock on the south link, but if it's not available immediately we need to know pronto
        lock = self.getLockNonBlocking('South Link Lock', loco)
        if lock == False:
            # stop the train
            self.gradualHalt(self.t1, 2)
            # wait for a lock
            lock = self.getLock('South Link Lock')
            if lock == False :
                return False
        else :
            # we got a lock
            self.waitMsec(250)
            # check we still have it
            rc = self.checkLock(lock, loco)
            if rc == False :
                # we lost it, abort!
                self.t1.setSpeedSetting(0)
                print loco, "race conditions on South Link Lock?"
                return False

        # into the sidings
        routes = ['Sth Fast Inner', 'Back Passage']
        rc = self.shortJourney(self.t1, True, 'FPK P7', 'Back Passage', 0.2, 0.1, 5, routes = routes, lock = lock)
        

        stop = time.time()
        print "route took", stop - start, 'seconds'

        return False
        
        
		

LocoEurostarSth2Nth().start()
