import jmri
import time

class StartUp :
    def do(self) :
    
        self.powerState = powermanager.getPower()
        if self.powerState != jmri.PowerManager.ON :
            powermanager.setPower(jmri.PowerManager.ON)
            time.sleep(1)
    
        r = None
        tries = 0
        while r == None and tries < 10 :        
            r = routes.getRoute('StartUp')
            if r == None:
                tries += 1
                print "tries:", tries
                time.sleep(1)
                next

        r.activateRoute()
        r.setRoute()

        print "StartUp done."

StartUp().do()
