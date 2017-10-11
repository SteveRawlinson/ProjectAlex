import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
from jmri_bindings import *
from myroutes import *

class Class37Sth2NthTrack4(alex.Alex):

    def __init__(self, loc, memory):
        self.loco = loc
        self.memory = memory

    def handle(self):

