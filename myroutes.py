SOUTH_SIDINGS = ['FP sidings', 'Sth Sidings 1', 'Sth Sidings 2', 'Sth Sidings 3', 'Sth Sidings 4', 'Sth Sidings 5']
NORTH_SIDINGS = ['Nth Siding 1', 'Nth Sidings 2', 'Nth Sidings 3', 'Nth Sidings 4', 'Nth Sidings 5']

CLEANER_SIDING_TIME = {
    'Nth Siding 1': 7.3, 'Nth Sidings 2': 8.3, 'Nth Sidings 3': 7.1, 'Nth Sidings 4': 12.5, 'Nth Sidings 5': 9.7,
    'FP sidings': 3.2, 'Sth Sidings 1': 9.5, 'Sth Sidings 2': 9, 'Sth Sidings 3': 7.8, 'Sth Sidings 4': 7, 'Sth Sidings 5': 7
}

NORTH_REVERSE_LOOP = 'Nth Reverse Loop'
SOUTH_REVERSE_LOOP = 'Sth Reverse Loop'

DEBUG = True

# Jack status codes
NORMAL = 0
STOPPING = 1
ESTOP = 2

# loco status
SIDINGS = 1
MOVING = 2

# ends of the track
NORTH = 0
SOUTH = 1

# direction constants
NORTHBOUND = 0
SOUTHBOUND = 1

IRSENSORS = {
    "Sth Sidings 1": "LS61",
    "Sth Sidings 2": "LS62",
    "Sth Sidings 3": "LS32",
    "Sth Sidings 4": "LS31",
    "Sth Sidings 5": "LS31",
    "FP sidings": "LS25",
    "Nth Siding 1": "LS27",
    "Nth Sidings 2": "LS28",
    "Nth Sidings 3": "LS29",
    "Nth Sidings 4": "LS57",
    "Nth Sidings 5": "LS57",
    NORTH_REVERSE_LOOP: "LS58",
    SOUTH_REVERSE_LOOP: "LS26",
    "North Link Clear": "LS63",
    "South Link Clear": "LS59",
    "South Sidings Clear": "LS30"
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
    [3, False, False, ['FPK P1', 'AAP P4', 'PAL P1'], 'LH1'],
    [3, False, False, ['FPK P2', 'AAP P3', 'PAL P2'], 'LH4'],
    [3, False, False, ['FPK P3', 'AAP P2', 'NSG P1'], 'LH2'],
    [3, False, False, ['FPK P4', 'AAP P1', 'NSG P2'], 'LH5'],
    [1, True, False, ['FPK P7', 'Sth Fast Inner 2', 'Nth Fast Inner 1'], 'LH3'],
    [1, True, False, ['FPK P8', 'Nth Fast Outer 2', 'Nth Fast Outer 1'], 'LH103']
]

# A hash of hashes. Keys are either a loco's dcc addr (eg. 68) or the name of
# a BR class (eg. "class150"). Values are a hash of string -> float where the
# string describes the speed and the float is the value to send to the throttle

SPEEDMAP = {
    # Mallard
    68: {'fast': 0.7, 'medium': 0.5, 'slow': 0.35},
    # class 150s
    "class150": {'fast': 0.6, 'medium': 0.35, 'slow': 0.25, 'north interlink northbound': 0.6},
    # Javelin
    5004: {'fast': 0.3, 'bend': 0.2, 'medium': 0.2, 'slow': 0.1, 'south link to layout': 'fast', 'off track north': 'fast'},
    # Eurostar
    3213: {'fast': 0.3, 'bend': 0.2, 'medium': 0.2, 'slow': 0.1, 'south link to layout': 'fast', 'off track north': 'fast'},
    # Ave Talgo
    6719: {'fast': 0.4, 'bend': 'fast', 'medium': 0.25, 'slow': 0.2, 'north sidings exit': 'fast', 'track to north link': 'fast', 'north link to sidings': 0.3, 'north sidings entry': 0.2,
           'track to south link': 0.4, 'south sidings exit': 0.2, 'south link to layout': 'fast', 'off track north': 'fast'},
    # class 91 virgin
    1124: {'fast': 0.5, 'bend': 0.3, 'medium': 0.35, 'slow': 0.2, 'south link to layout': 'fast', 'off track north': 'fast', 'south link wait for route': 0.1,
           'north interlink northbound': 0.5, 'track to south link:': 0.5},
    # class 47
    "class47": {'fast': 0.6, 'medium': 0.35, 'slow': 0.25},
    # Underground
    1087: {'fast': 0.5, 'medium': 0.3, 'slow': 0.2, 'exit south sidings': 0.3}
}

SLOWTIMEMAP = {
    # class 47
    "class47": {'FPK P7': 8, "NORTH FAST": 13, "NSG P2": 5, "Nth Fast Outer 1": 5, "FPK P3": 5},
    # Mallard
    "classA4": {'FPK P7': 13, "NORTH FAST": 15, 'FPK P8': 17, "FPK P4": 5, "NSG P2": 6, "PAL P2": 5 , "FPK P2": 2, "FPK P3": 3},
    # class 150s
    "class150": {"FPK P2": 3, "AAP P3": 1.5, "PAL P2": 2, "North Link": 4, "PAL P1": 4, "AAP P4": 3, "FPK P1": 10, "FPK P4": 2, "AAP P1": 1, "NSG P2": 3,
                 "FPK P3": 8, "AAP P2": 3, "NSG P1": 5},
    # Underground
    1087: {"FPK P3": 11, "AAP P2": 4, "NSG P1": 8, "PAL P1": 6, "AAP P4": 7, "FPK P1": 13, "FPK P4": 5, "AAP P1": 5, "NSG P2": 3, "FPK P2": 8,
           "AAP P3": 7, "PAL P2": 5, "North Link": 4},
    # Javelin
    5004: {'North Link': 5, 'FPK P7': 5, "Nth fast Outer 1": 5},
    # Ave Talgo
    6719: {'Nth Fast Outer 1': 3}
}

TROUBLESOME_TURNOUTS = [] # ['LT17', 'LT20', 'LT23']
