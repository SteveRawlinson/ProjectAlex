import alex
from jmri_bindings import *
import loco
from javax.swing import JOptionPane


# statuses
NORMAL = 0
STOPPING = 1
ESTOP = 2

class MoveLocosToSidings(alex.Alex):

    def __init__(self):
        self.locos = []
        self.tracks = []
        self.memory = None
        self.knownLocation = None

    def go(self):

        self.initTracks()

        # set jeckstatus()
        old_status = self.getJackStatus()
        mem = memories.provideMemory('IMJACKSTATUS')
        mem.setValue(NORMAL)

        # If there's a loco on the North Link then that one needs to be
        # moved before any of the others. This var keeps track of which
        # loco it is
        northLinkLoco = None

        # gather up the locos
        addresses = []
        for t in self.tracks:
            for b in t.blocks:
                blk = blocks.getBlock(b)
                self.debug('checking block ' + b)
                if blk.getState() == OCCUPIED:
                    addr = blk.getValue()
                    if addr is None or addr == '':
                        addr = JOptionPane.showInputDialog("DCC addr of loco in: " + blk.getUserName())
                    addr = int(addr)
                    if not addr in addresses:
                        self.debug("getting loco for " + str(addr))
                        l = loco.Loco(addr)
                        self.debug("getting throttle for " + str(addr))
                        self.getLocoThrottle(l)
                        self.locos.append(l)
                        l.setBlock(blk)
                        addresses.append(addr)
                        if blk.getUserName() == 'North Link':
                            northLinkLoco = l

        # keep looping until we've gone through the whole list
        # and failed on all of them
        locolist = self.locos[:]
        if northLinkLoco and northLinkLoco in locolist:
            # move it to the front of the queue
            locolist.remove(northLinkLoco)
            locolist.insert(0, northLinkLoco)
        keepGoing = True
        while keepGoing:
            keepGoing = False
            for l in locolist:
                if l.isInSidings():
                    continue
                self.debug("trying to move " + l.nameAndAddress())
                self.loco = l
                rc = self.moveToASiding()
                if rc:
                    locolist.remove(l)
                    keepGoing = True

        mem = memories.provideMemory('IMJACKSTATUS')
        mem.setValue(old_status)
        return False

MoveLocosToSidings().start()