SOUTH_SIDINGS = ['FP sidings', 'Sth Sidings 1', 'Sth Sidings 2', 'Sth Sidings 3', 'Sth Sidings 5']
NORTH_SIDINGS = ['Nth Siding 1', 'Nth Sidings 2', 'Nth Sidings 3', 'Nth Sidings 4', 'Nth Sidings 5']
NORTH_REVERSE_LOOP = 'Nth Reverse Loop'
SOUTH_REVERSE_LOOP = 'Sth Reverse Loop'


IRSENSORS = {
    "Sth Sidings 1": "LS61",
    "Sth Sidings 2": "LS62",
    "Sth Sidings 3": "LS32",
    "Sth Sidings 4": None,
    "Sth Sidings 5": "LS31",
    "FP sidings": "LS25",
    "Nth Siding 1": "LS27",
    "Nth Sidings 2": "LS28",
    "Nth Sidings 3": "LS29"
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
            "Nth Fast Outer 1": ["Nth Fast Outer"]

            }

# fields are:
# stops: number of stations
# fast: true if this is a high speed track
TRACKS = [
    [3, False],
    [3, False],
    [3, False],
    [3, False],
    [1, True],
    [1, True]
]