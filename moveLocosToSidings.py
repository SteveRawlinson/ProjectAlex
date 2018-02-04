import alex
from jmri_bindings import *
import loco
from javax.swing import JOptionPane

class MoveLocosToSidings(alex.Alex):

    def __init__(self):
        self.locos = []
        self.tracks = []
        self.memory = None

    def go(self):

        self.initTracks()

        # gather up the locos
        for t in self.tracks:
            for b in t.blocks:
                blk = blocks.getBlock(b)
                if blk.getState() == OCCUPIED:
                    addr = blk.getValue()
                    if addr is None or addr == '':
                        addr = JOptionPane.showInputDialog("DCC addr of loco in: " + blk.getUserName())
                    self.debug("getting loco for " + str(addr))
                    l = loco.Loco(addr)
                    self.debug("getting throttle for " + str(addr))
                    self.getLocoThrottle(l)
                    self.locos.append(l)
                    l.setBlock(blk)

        # keep looping until we've gone through the whole list
        # and failed on all of them
        locolist = self.locos[:]
        keepGoing = True
        while keepGoing:
            keepGoing = False
            for l in locolist:
                self.debug("trying to move " + l.nameAndAddress())
                self.loco = l
                rc = self.moveToASiding()
                if rc:
                    locolist.remove(l)
                    keepGoing = True

        print "MoveLocosToSidings all done."
        return False

MoveLocosToSidings().start()