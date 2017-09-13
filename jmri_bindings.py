import jmri

# JMRI default managers
turnouts     = jmri.InstanceManager.getDefault(jmri.TurnoutManager)
sensors      = jmri.InstanceManager.getDefault(jmri.SensorManager)
signals      = jmri.InstanceManager.getDefault(jmri.SignalHeadManager)
masts        = jmri.InstanceManager.getDefault(jmri.SignalMastManager)
lights       = jmri.InstanceManager.getDefault(jmri.LightManager)
dcc          = jmri.InstanceManager.getDefault(jmri.CommandStation)
reporters    = jmri.InstanceManager.getDefault(jmri.ReporterManager)
memories     = jmri.InstanceManager.getDefault(jmri.MemoryManager)
routes       = jmri.InstanceManager.getDefault(jmri.RouteManager)
blocks       = jmri.InstanceManager.getDefault(jmri.BlockManager)
powermanager = jmri.InstanceManager.getDefault(jmri.PowerManager)
programmers  = jmri.managers.WarningProgrammerManager(jmri.InstanceManager.programmerManagerInstance())
addressedProgrammers = jmri.InstanceManager.getDefault(jmri.AddressedProgrammerManager)
globalProgrammers = jmri.InstanceManager.getDefault(jmri.GlobalProgrammerManager)
shutdown     = jmri.InstanceManager.getDefault(jmri.ShutDownManager)
audio        = jmri.InstanceManager.getDefault(jmri.AudioManager)
layoutblocks = jmri.InstanceManager.getDefault(jmri.jmrit.display.layoutEditor.LayoutBlockManager)
warrants     = jmri.InstanceManager.getDefault(jmri.jmrit.logix.WarrantManager)


# constants
ACTIVE = jmri.Sensor.ACTIVE
INACTIVE = jmri.Sensor.INACTIVE
OCCUPIED = jmri.Block.OCCUPIED