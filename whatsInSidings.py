import alex
from myroutes import *
from jmri_bindings import *

class WhatsInSidings(alex.Alex):
    def __init__(self):
        self.locos = []

    def go(self):
        self.whatsInSidings(NORTH_SIDINGS + SOUTH_SIDINGS)

WhatsInSidings().start()