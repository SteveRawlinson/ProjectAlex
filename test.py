import jmri
import time
import sys
sys.path.append('C:\\Users\\steve\\JMRI\\jython')
import alex
import loco
import lock
from jmri_bindings import *
from myroutes import *

DEBUG = True

class Mytest(alex.Alex):

    def __init__(self):
        self.locos =[]

    def do(self):
        print "here"
        self.whatsInSidings(SOUTH_SIDINGS)


Mytest().do()

