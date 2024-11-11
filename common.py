import threading

admin = True

# Constants
HUD_POSITION_FILE = 'hud_positions.json'

# Global variables
players = []           # List to store player objects
hud_windows = []       # List to store HUDWindow objects
selected_units_dict = {}    # Dict to store units for the unitSelection HUD
data_lock = threading.Lock()
process_handle = None  # Handle for the game process
control_panel = None   # Reference to the ControlPanel instance
data_update_thread = None  # Reference to the DataUpdateThread instance
game_path = None    # Game path


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

factions = ['Allied', 'Soviet', 'Yuri', 'Other']

unit_types = ['Infantry', 'Structure', 'Tank', 'Naval', 'Aircraft']


def name_to_path(name):
    return 'cameos/png/' + name + '.png'

def country_name_to_faction(country_name):
    if country_name in ['Americans', 'Alliance', 'French', 'Germans', 'British']:
        return 'Allied'
    elif country_name in ['Africans', 'Arabs', 'Confederation', 'Russians']:
        return 'Soviet'
    elif country_name == 'YuriCountry':
        return 'Yuri'
    else:
        return 'Unknown'