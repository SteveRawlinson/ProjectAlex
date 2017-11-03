SOUTH_SIDINGS = ['FP sidings', 'Sth Sidings 1', 'Sth Sidings 2', 'Sth Sidings 3', 'Sth Sidings 5']
NORTH_SIDINGS = ['Nth Siding 1', 'Nth Sidings 2', 'Nth Sidings 3', 'Nth Sidings 4', 'Nth Sidings 5']
NORTH_REVERSE_LOOP = 'Nth Reverse Loop'
SOUTH_REVERSE_LOOP = 'Sth Reverse Loop'

# Jack status codes
NORMAL = 0
STOPPING = 1
ESTOP = 2


IRSENSORS = {
    "Sth Sidings 1": "LS61",
    "Sth Sidings 2": "LS62",
    "Sth Sidings 3": "LS32",
    "Sth Sidings 4": None,
    "Sth Sidings 5": "LS31",
    "FP sidings": "LS25",
    "Nth Siding 1": "LS27",
    "Nth Sidings 2": "LS28",
    "Nth Sidings 3": "LS29",
    "Nth Sidings 4": "LS57",
    "Nth Sidings 5": "LS57",
    NORTH_REVERSE_LOOP: "LS58",
    SOUTH_REVERSE_LOOP: "LS26"
}

ROUTEMAP = {
            "Sth Sidings 1": ["Sth Sidings 1", "Back Passage"],
            "Sth Sidings 2": ["Sth Sidings 2", "Back Passage"],
            "Sth Sidings 3": ["Sth Sidings 3", "Back Passage"],
            "Sth Sidings 4": ["Sth Sidings 4", "Back Passage"],
            "Sth Sidings 5": ["Sth Sidings 5", "Back Passage"],
            "FP sidings": ["Sth Sidings"],
            "PAL P1": ["Hertford Nth Inner"],
            "PAL P2": ["Hertford Nth Outer"],
            "FPK P1": ["Sth Hertford Inner"],
            "FPK P2": ["Sth Hertford Outer"],
            "FPK P3": ["Sth Welwyn Inner"],
            "FPK P4": ["Sth Welwyn Outer"],
            "FPK P7": ["Sth Fast Inner"],
            "FPK P8": ["Sth Fast Outer"],
            "NSG P1": ["Welwyn Inner"],
            "NSG P2": ["Welwyn Outer"],
            "Nth Fast Inner 1": ["Nth Fast Inner"],
            "Nth Fast Outer 1": ["Nth Fast Outer"],
            NORTH_REVERSE_LOOP: ["Nth Reverse Loop Entry", "Nth Reverse Loop Exit"],
            SOUTH_REVERSE_LOOP: ["Sth Reverse Loop Entry", "Sth Reverse Loop Exit"],
            "North Link": [],
            "South Link": []
            }

# fields are:
# stops: number of stations
# fast: true if this is a high speed track
# u/s: true if the track is undergoing maintenance
# blocks: list of blocks on the track, going from South to North
TRACKS = [
    [3, False, False, ['FPK P1', 'AAP P4', 'PAL P1']],
    [3, False, False, ['FPK P2', 'AAP P3', 'PAL P2']],
    [3, False, False, ['FPK P3', 'AAP P2', 'NSG P1']],
    [3, False, False, ['FPK P4', 'AAP P1', 'NSG P2']],
    [1, True, False, ['FPK P7', 'Sth Fast Inner 2', 'Nth Fast Inner 1']],
    [1, True, False, ['FPK P8', 'Nth Fast Outer 2', 'Nth Fast Outer 1']]
]

CLASS_47_SPEEDS = [0.6, 0.35, 0.2]