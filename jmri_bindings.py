import jmri

# JMRI default managers
turnouts     = jmri.InstanceManager.turnoutManagerInstance()
sensors      = jmri.InstanceManager.sensorManagerInstance()
signals      = jmri.InstanceManager.signalHeadManagerInstance()
masts        = jmri.InstanceManager.signalMastManagerInstance()
lights       = jmri.InstanceManager.lightManagerInstance()
dcc          = jmri.InstanceManager.commandStationInstance()
reporters    = jmri.InstanceManager.reporterManagerInstance()
memories     = jmri.InstanceManager.memoryManagerInstance()
routes       = jmri.InstanceManager.routeManagerInstance()
blocks       = jmri.InstanceManager.blockManagerInstance()
powermanager = jmri.InstanceManager.powerManagerInstance()
programmers  = jmri.InstanceManager.programmerManagerInstance()
shutdown     = jmri.InstanceManager.shutDownManagerInstance()
audio        = jmri.InstanceManager.audioManagerInstance()
layoutblocks = jmri.InstanceManager.getDefault(jmri.jmrit.display.layoutEditor.LayoutBlockManager)
warrants     = jmri.InstanceManager.getDefault(jmri.jmrit.logix.WarrantManager)

# constants
ACTIVE = jmri.Sensor.ACTIVE
INACTIVE = jmri.Sensor.INACTIVE
OCCUPIED = jmri.Block.OCCUPIED