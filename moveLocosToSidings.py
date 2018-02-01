import alex
from jmri_bindings import *
import util
import loco


class MoveLocosToSidings(alex.Alex):

    def __init__(self):
        self.locos = []
        self.tracks = []

    def go(self):

        self.initTracks()

        # gather up the locos
        for t in self.tracks:
            for b in t.blocks:
                blk = blocks.getBlock(b)
                if blk.getState() == OCCUPIED:
                    addr = blk.getValue()
                    if addr is None or addr == '':
                        addr = JOptionPane.showInputDialog("DCC loco in: " + s)
                    l = loco.Loco(addr)
                    self.getLocoThrottle(l)
                    self.locos.append(l)

        # keep looping until we've gone through the whole list
        # and failed on all of them
        locolist = self.locos[:]
        keepGoing = True
        while keepGoing:
            keepGoing = False
            for l in locolist:
                self.debug("trying to move " + l.nameAndSAddress())
                rc = self.moveToASiding()
                if rc:
                    locolist.remove(l)
                    keepGoing = True

        return False
