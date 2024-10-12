import threading

# Constants
HUD_POSITION_FILE = 'hud_positions.json'

# Global variables
players = []           # List to store player objects
hud_windows = []       # List to store HUDWindow objects
selected_units_dict = {}    # Dict to store units for the unitSelection HUD
data_lock = threading.Lock()
hud_positions = {}     # Dictionary to store HUD positions and settings
process_handle = None  # Handle for the game process
control_panel = None   # Reference to the ControlPanel instance
data_update_thread = None  # Reference to the DataUpdateThread instance
names = {
    "Allied": {
        "Infantry": [
            "GI",
            "GGI",
            "Allied Dog",
            "Allied Engineer",
            "Chrono Legionnaire",
            "Spy",
            "Rocketeer",
            "Tanya",
            "Navy Seal"
        ],
        "Structure": [
            "Allied Power Plant",
            "SpySat",
            "Allied Naval Yard",
            "Allied Barracks",
            "ChronoSphere",
            "Allied Service Depot",
            "Gap Generator",
            "Grand Cannon",
            "Ore Purifier",
            "PillBox",
            "Allied AFC",
            "Allied Battle Lab",
            "Robot Control Center",
            "Allied Ore Refinery",
            "Weather Controller",
            "Allied War Factory"
        ],
        "Tank": [
            "Grizzly",
            "Chrono Miner",
            "Battle Fortress",
            "IFV",
            "Allied MCV",
            "Prism Tank",
            "Tank Destroyer",
            "Robot Tank",
            "Mirage Tank",
            "NightHawk Transport"
        ],
        "Naval": [
            "Agis Cruiser",
            "Aircraft Carrier",
            "Destroyer",
            "Dolphin",
            "Allied Amphibious Transport"
        ],
        "Aircraft": [
            "Black Eagle",
            "Harrier"
        ]
    },
    "Soviet": {
        "Infantry": [
            "conscript",
            "Desolator",
            "Boris",
            "Soviet Dog",
            "Soviet Engineer",
            "Flak Trooper",
            "Ivan",
            "Terrorist"
        ],
        "Structure": [
            "Soviet Barracks",
            "Battle Bunker",
            "Flak Cannon",
            "Industrial Plant",
            "Sentry Gun",
            "Iron Curtain",
            "Nuclear Missile Launcher",
            "Soviet War Factory",
            "Tesla Reactor",
            "Sov Radar",
            "Nuclear Reactor",
            "Sov Service Depot",
            "Sov Ore Ref",
            "Tesla Coil",
            "Sov Naval Yard"
        ],
        "Tank": [
            "Rhino Tank",
            "Terror Drone",
            "Flak Track",
            "War Miner",
            "V3 Rocket Launcher",
            "Apoc",
            "Siege Chopper",
            "Soviet MCV",
            "Kirov",
            "Demolition truck"
        ],
        "Naval": [
            "Dreadnought",
            "Squid",
            "Soviet Amphibious Transport",
            "Typhoon attack sub",
            "Sea Scorpion"
        ],
        "Aircraft": []
    },
    "Yuri": {
        "Infantry": [
            "Initiate",
            "Virus",
            "Yuri Clone",
            "Yuri Prime",
            "Yuri Engineer",
            "Brute"
        ],
        "Structure": [
            "Yuri War Factory",
            "Yuri Barracks",
            "Cloning Vats",
            "Grinder",
            "Gattling Cannon",
            "Tank Bunker",
            "Yuri Radar",
            "Psychic Tower",
            "Psychic dominator",
            "Slave Miner Deployed",
            "Bio Reactor",
            "Yuri Battle Lab",
            "Yuri Naval Yard"
        ],
        "Tank": [
            "Gattling Tank",
            "Chaos Drone",
            "Disc",
            "Lasher",
            "Mastermind",
            "Magnetron",
            "Yuri MCV"
        ],
        "Naval": [
            "Boomer Sub",
            "Yuri Amphibious Transport"
        ],
        "Aircraft": []
    }
}

COLOR_NAME_MAPPING = {
    3: "yellow",
    5: "white",
    7: "gray",
    11: "red",
    13: "orange",
    15: "pink",
    17: "purple",
    21: "blue",
    25: "cyan",
    29: "green",
}

def name_to_path(name):
    return 'cameos/png/' + name + '.png'

