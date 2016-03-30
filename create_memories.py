import jmri

for name in layoutblocks.getSystemNameList():
    print "layoutblock system name:", name
    b = layoutblocks.getBySystemName(name)
    print "layoutblock usernmame:",  b.userName
    mem = memories.getMemory(b.userName)
    if mem == None:
        mem = memories.newMemory(b.userName)
        print "got new memory, system name:", mem.systemName
    b.setMemory(mem, b.userName)
    print "layoutblock memory name:", b.getMemoryName()
    print "layoutblock occupancy sensor name:", b.getOccupancySensor().getSystemName()
    

