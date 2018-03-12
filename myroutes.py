
from jmri_bindings import *

SOUTH_SIDINGS = ['FP sidings', 'Sth Sidings 1', 'Sth Sidings 2', 'Sth Sidings 3', 'Sth Sidings 4', 'Sth Sidings 5']
NORTH_SIDINGS = ['Nth Siding 1', 'Nth Sidings 2', 'Nth Sidings 3', 'Nth Sidings 4', 'Nth Sidings 5']

CLEANER_SIDING_TIME = {
    'Nth Siding 1': 11.31, 'Nth Sidings 2': 10.3, 'Nth Sidings 3': 10.5, 'Nth Sidings 4': 16.5, 'Nth Sidings 5': 14.3,
    'FP sidings': 6.0, 'Sth Sidings 1': 14.5, 'Sth Sidings 2': 13, 'Sth Sidings 3': 12, 'Sth Sidings 4': 11.5, 'Sth Sidings 5': 10
}

NORTH_REVERSE_LOOP = 'Nth Reverse Loop'
SOUTH_REVERSE_LOOP = 'Sth Reverse Loop'

DEBUG = True

LOGFILE = "C:\Users\steve\jmri.log"

# Jack status codes
NORMAL = 0
STOPPING = 1
ESTOP = 2
STOPPED = 3

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
            "Sth Sidings 1": ["Back Passage", "Sth Sidings 1"],
            "Sth Sidings 2": ["Back Passage", "Sth Sidings 2"],
            "Sth Sidings 3": ["Back Passage", "Sth Sidings 3"],
            "Sth Sidings 4": ["Back Passage", "Sth Sidings 4"],
            "Sth Sidings 5": ["Back Passage", "Sth Sidings 5"],
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
    [1, True, False, ['FPK P8', 'Nth Fast Outer 2', 'Nth Fast Outer 1'], 'LH6']
]

# A hash of hashes. Keys are either a loco's dcc addr (eg. 68) or the name of
# a BR class (eg. "class150"). Values are a hash of string -> float where the
# string describes the speed and the float is the value to send to the throttle

SPEEDMAP = {
    # Mallard
    68: {'fast': 0.7, 'medium': 0.5, 'slow': 0.35},
    # class 150s
    "class150": {'fast': 0.6, 'medium': 0.35, 'slow': 0.25, 'north interlink northbound': 0.6, 'north interlink southbound': 0.7},
    # Javelin
    5004: {'fast': 0.6, 'bend': 0.3, 'medium': 0.35, 'slow': 0.2, 'south link to layout': 'fast', 'off track north': 'fast', 'north link to layout': 'fast',
           'off track south': 'fast', 'south sidings entry': 'slow', "north fast outer 1 halting": 'slow'},
    # Eurostar
    3213: {'fast': 0.3, 'bend': 0.2, 'medium': 0.2, 'slow': 0.1, 'south link to layout': 'fast', 'off track north': 'fast', 'north link to layout': 'fast',
           'south sidings entry': 'slow', 'north sidings entry': 'slow', 'north link to sidings': 0.1, 'off track south partial lock': 0.2},
    # TGV
    4404: {'fast': 0.65, 'bend': 0.45, 'medium': 0.45, 'slow': 0.25, 'south link to layout': 'fast', 'off track north': 'fast', 'north link to layout': 'fast',
           'south sidings entry': 'slow', 'north sidings entry': 'slow', 'north link to sidings': 'slowf'},
    # ICE 3
    4030: {'fast': 0.7, 'bend': 0.55, 'medium': 0.55, 'slow': 0.3, 'south link to layout': 'fast', 'off track north': 'fast', 'north link to layout': 'fast',
           'south sidings entry': 'slow', 'north sidings entry': 'slow', 'north link to sidings': 'slow'},
    # Ave Talgo
    6719: {'fast': 0.5, 'bend': 'fast', 'medium': 0.35, 'slow': 0.25, 'north sidings exit': 'fast', 'track to north link': 'fast', 'north link to sidings': 0.35,
           'north sidings entry': 0.3, 'off track south': 0.5, 'south sidings exit': 0.3, 'south link to layout': 'fast', 'off track north': 'fast', 'north interlink southbound': 'fast',
           'north link to layout': 'fast'},
    # class 91 virgin
    1124: {'fast': 0.5, 'bend': 0.3, 'medium': 0.35, 'slow': 0.2, 'south link to layout': 'fast', 'off track north': 'fast', 'south link wait for route': 0.1,
           'north interlink northbound': 0.5, 'off track south:': 0.5, 'north sidings entry': 0.1, 'north link to sidings': 'slow', 'north interlink southbound': 'fast',
           'north link to layout': 'fast', 'fast going slow': 0.27, 'south sidings exit': 0.3, 'FPK P3': 4, 'south sidings entry': 'slow'},
    # class 43 virgin
    3314: {'fast': 0.5, 'bend': 0.3, 'medium': 0.35, 'slow': 0.2, 'south link to layout': 'fast', 'off track north': 'fast', 'south link wait for route': 0.1,
           'north interlink northbound': 0.5, 'off track south:': 0.5, 'north sidings entry': 0.1, 'north link to sidings': 'slow', 'north interlink southbound': 'fast',
           'north link to layout': 'fast', 'fast going slow': 0.27, 'south sidings exit': 0.3, 'FPK P3': 4, 'south sidings entry': 'slow'},

    # class 47
    "class47": {'fast': 0.6, 'medium': 0.35, 'slow': 0.25, 'north interlink southbound': 'fast'},
    # Underground
    1087: {'fast': 0.7, 'medium': 0.3, 'slow': 0.2, 'exit south sidings': 0.3, 'north sidings exit': 0.7, 'north interlink southbound': 0.7, 'north interlink northbound': 0.7}
}

SLOWTIMEMAP = {
    # class 47
    "class47": {'FPK P7': 8, "NORTH FAST": 13, "NSG P2": 5, "Nth Fast Outer 1": 7, "FPK P3": 5, "FPK P1": 7, "PAL P2": 3},
    # Mallard
    "classA4": {'FPK P7': 13, "NORTH FAST": 15, 'FPK P8': 17, "FPK P4": 5, "NSG P2": 6, "PAL P2": 5 , "FPK P2": 5, "FPK P3": 4},
    # class 150s
    "class150": {"FPK P2": 3, "AAP P3": 1.5, "PAL P2": 2, "North Link": 4, "PAL P1": 3, "AAP P4": 2, "FPK P1": 10, "FPK P4": 2, "AAP P1": 1, "NSG P2": 3,
                 "FPK P3": 8, "AAP P2": 3, "NSG P1": 4},
    # Underground
    1087: {"FPK P3": 9, "AAP P2": 4, "NSG P1": 2.5, "PAL P1": 5, "AAP P4": 5, "FPK P1": 11, "FPK P4": 3, "AAP P1": 3, "NSG P2": 3, "FPK P2": 4,
           "AAP P3": 4, "PAL P2": 4, "North Link": 4},
    # Javelin
    5004: {'North Link': 5, 'FPK P7': 5, "Nth Fast Outer 1": 1},
    # Ave Talgo
    6719: {'Nth Fast Outer 1': 6, "FPK P7": 6},
    # Eurostar
    3213: {"FPK P7": 5, "Nth Fast Outer 1": 2},
    # TGV
    4404: {"FPK P7": 7, "Nth Fast Outer 1": 3},
    # ICE 3
    4030: {"FPK P7": 7, "Nth Fast Outer 1": 1},
    # Virgin class 91
    1124: {"FPK P7": 6, "Nth Fast Outer 1": 0},
    # Virgin class 43
    3314: {"FPK P7": 6, "Nth Fast Outer 1": 0},
}

TROUBLESOME_TURNOUTS = [] # ['LT17', 'LT20', 'LT23']

TRACKSENSORS = {1: "IS41", 2: "IS42", 3: "IS43", 4: "IS44", 5: "IS45", 6: "IS46"}

LN_SLOT_STATUS = {LOCO_IDLE: 'idle', LOCO_COMMON: 'common', LOCO_IN_USE: 'in use', LOCO_FREE: 'free'}