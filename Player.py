import ctypes
import logging
import traceback

from PySide6.QtGui import QColor

from common import COLOR_NAME_MAPPING, country_name_to_faction

# Constants
MAXPLAYERS = 8
INVALIDCLASS = 0xffffffff

INFOFFSET = 0x557c
AIRCRAFTOFFSET = 0x5590
TANKOFFSET = 0x5568
BUILDINGOFFSET = 0x5554

CREDITSPENT_OFFSET = 0x2dc
BALANCEOFFSET = 0x30c
USERNAMEOFFSET = 0x1602a
ISWINNEROFFSET = 0x1f7
ISLOSEROFFSET = 0x1f8

POWEROUTPUTOFFSET = 0x53a4
POWERDRAINOFFSET = 0x53a8

HOUSETYPECLASSBASEOFFSET = 0x34
COUNTRYSTRINGOFFSET = 0x24

COLORSCHEMEOFFSET = 0x16054

# Define the mappings of offsets to unit, infantry, and building names
infantry_offsets = {
    0x0: "GI", 0x4: "conscript", 0x8: "tesla trooper", 0xc: "Allied Engineer", 0x10: "Rocketeer",
    0x14: "Navy Seal", 0x18: "Yuri Clone", 0x1c: "Ivan", 0x20: "Desolator", 0x24: "Soviet Dog",
    0x3c: "Chrono Legionnaire", 0x40: "Spy", 0x50: "Yuri Prime", 0x54: "Sniper", 0x60: "Tanya",
    0x6c: "Soviet Engineer", 0x68: "Terrorist", 0x70: "Allied Dog", 0xb4: "Yuri Engineer",
    0xb8: "GGI", 0xbc: "Initiate", 0xc0: "Boris", 0xc4: "Brute", 0xc8: "Virus",
}

tank_offsets = {
    0x0: "Allied MCV", 0x4: "War Miner", 0x8: "Apoc", 0x10: "Soviet Amphibious Transport", 0xc: "Rhino Tank",
    0x24: "Grizzly", 0x34: "Aircraft Carrier", 0x38: "V3 Rocket Launcher", 0x3c: "Kirov",
    0x40: "Terror Drone", 0x44: "Flak Track", 0x48: "Destroyer", 0x4c: "Typhoon attack sub", 0x50: "Aegis Cruiser",
    0x54: "Allied Amphibious Transport", 0x58: "Dreadnought", 0x5c: "NightHawk Transport", 0x60: "Squid",
    0x64: "Dolphin", 0x68: "Soviet MCV", 0x6c: "Tank Destroyer", 0x7c: "Lasher", 0x84: "Chrono Miner",
    0x88: "Prism Tank", 0x90: "Sea Scorpion", 0x94: "Mirage Tank", 0x98: "IFV", 0xa4: "Demolition truck",
    0xdc: "Yuri Amphibious Transport", 0xe0: "Yuri MCV", 0xe4: "Slave miner undeployed", 0xf0: "Gattling Tank",
    0xf4: "Battle Fortress", 0xfc: "Chaos Drone", 0xf8: "Magnetron", 0x108: "Boomer", 0x10c: "Siege Chopper",
    0x114: "Mastermind", 0x118: "Disc", 0x120: "Robot Tank",
}

structure_offsets = {
    0x0: "Allied Power Plant", 0x4: "Allied Ore Refinery", 0x8: "Allied Con Yard", 0xc: "Allied Barracks",
    0x14: "Allied service Depot", 0x18: "Allied Battle Lab", 0x1c: "Allied War Factory", 0x24: "Tesla Reactor",
    0x28: "Sov Battle lab", 0x2c: "sov barracks", 0x34: "Sov Radar", 0x38: "Soviet War Factory",
    0x3c: "Sov Ore Ref", 0x48: "Yuri Radar", 0x50: "Sentry Gun", 0x54: "Patriot Missile",
    0x5c: "Allied Naval Yard", 0x60: "Iron Curtain", 0x64: "sov con yard", 0x68: "Sov Service Depot",
    0x6c: "ChronoSphere", 0x74: "Weather Controller", 0xd4: "Tesla Coil", 0xd8: "Nuclear Missile Launcher",
    0xf4: "Sov Naval Yard", 0xf8: "SpySat Uplink", 0xfc: "Gap Generator", 0x100: "Grand Cannon",
    0x104: "Nuclear Reactor", 0x108: "PillBox", 0x10c: "Flak Cannon", 0x11c: "Oil", 0x120: "Cloning Vats",
    0x124: "Ore Purifier", 0x1a4: "Allied AFC", 0x21c: "American AFC", 0x2dc: "Blitz oil (psychic sensor)",
    0x4b0: "Yuri Con Yard", 0x4b4: "Bio Reactor", 0x4b8: "Yuri Barracks", 0x4bc: "Yuri War Factory",
    0x4c0: "Yuri Naval Yard", 0x4c8: "Yuri Battle Lab", 0x4d0: "Gattling Cannon", 0x4d4: "Psychic Tower",
    0x4d8: "Industrial Plant", 0x4dc: "Grinder", 0x4e0: "Genetic Mutator", 0x4ec: "Psychic dominator",
    0x558: "Tank Bunker", 0x590: "Robot Control Center", 0x594: "Slave Miner Deployed", 0x59c: "Battle Bunker",
}

aircraft_offsets = {
    0x4: "Harrier",
    0x1c: "Black Eagle"
}

import ctypes
import logging
import traceback


class ProcessExitedException(Exception):
    """Custom exception to indicate that the game process has exited."""
    pass


class Player:
    """Represents a game player, handling dynamic data read from memory."""

    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.process_handle = process_handle
        self.real_class_base = real_class_base

        # Player details
        self.username = ctypes.create_unicode_buffer(0x20)
        self.color = ""
        self.color_name = ''
        self.country_name = ctypes.create_string_buffer(0x40)
        self.faction = 'Unknown'

        # Player status flags
        self.is_winner = False
        self.is_loser = False

        # Resource and power attributes
        self.balance = 0
        self.spent_credit = 0
        self.power_output = 0
        self.power_drain = 0
        self.power = self.power_output - self.power_drain

        # Unit counts by type
        self.infantry_counts = {}
        self.tank_counts = {}
        self.building_counts = {}
        self.aircraft_counts = {}

        # Memory pointers for unit arrays
        self.unit_array_ptr = None
        self.building_array_ptr = None
        self.infantry_array_ptr = None
        self.aircraft_array_ptr = None

        # Address offsets for memory operations
        self.test_addresses = {
            "infantry": self.real_class_base + 0x0b30,
            "unit": self.real_class_base + 0x1338,
            "building": self.real_class_base + 0x1b40,
            "aircraft": self.real_class_base + 0x328
        }

        # Initialize memory pointers
        self.initialize_pointers()

    # Memory Initialization Methods
    # ------------------------------------------------------------------------

    def initialize_pointers(self):
        """Initializes pointers for the arrays of units, buildings, and infantry."""
        try:
            self.unit_array_ptr = self._initialize_pointer(TANKOFFSET, "unit")
            self.building_array_ptr = self._initialize_pointer(BUILDINGOFFSET, "building")
            self.infantry_array_ptr = self._initialize_pointer(INFOFFSET, "infantry")
            self.aircraft_array_ptr = self._initialize_pointer(AIRCRAFTOFFSET, "aircraft")
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Error initializing pointers for player {self.index}: {e}")
            traceback.print_exc()

    def _initialize_pointer(self, offset, pointer_name):
        """Helper function to initialize a pointer based on an offset."""
        pointer_address = self.real_class_base + offset
        pointer_data = read_process_memory(self.process_handle, pointer_address, 4)
        if pointer_data:
            pointer_value = ctypes.c_uint32.from_buffer_copy(pointer_data).value
            logging.debug(f"Initialized {pointer_name} array pointer: {pointer_value}")
            return pointer_value
        return None

    # Data Management Methods
    # ------------------------------------------------------------------------

    def read_and_store_inf_units_buildings(self, category_dict, array_ptr, count_type):
        """Helper to read and store values for infantry, tanks, or buildings from memory."""
        if array_ptr is None:
            return {}

        counts = {}
        try:
            for offset, name in category_dict.items():
                specific_address = array_ptr + offset
                test_address = self.test_addresses[count_type] + offset

                count_data = read_process_memory(self.process_handle, specific_address, 4)
                test_data = read_process_memory(self.process_handle, test_address, 4)

                if count_data and test_data:
                    count = int.from_bytes(count_data, byteorder='little')
                    test = int.from_bytes(test_data, byteorder='little')
                    if name == "Blitz oil (psychic sensor)" and 15 > count > 0:
                        counts[name] = count
                    elif name == "Oil":
                        counts[name] = count
                        self.write_oil_count_to_file(count)
                    elif count <= test:
                        counts[name] = count
                    else:
                        counts[name] = 0
                else:
                    logging.warning(f"Failed to read memory for {name}, count_data or test_data is None.")
            return counts
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in read_and_store_inf_units_buildings for player {self.username.value}: {e}")
            traceback.print_exc()
            return counts

    def write_oil_count_to_file(self, oil_count):
        """Writes the oil count to a text file based on the player's color."""
        filename = f"{self.color_name}_oil_count.txt"
        try:
            with open(filename, 'w') as file:
                file.write(str(oil_count))
            logging.debug(f"Wrote oil count {oil_count} to file {filename}")
        except Exception as e:
            logging.error(f"Failed to write oil count to file: {e}")

    def update_dynamic_data(self):
        """Updates player data such as balance, spent credit, power, and unit counts."""
        try:
            logging.debug(f"Updating dynamic data for player {self.index}")
            self._update_resources()
            self._update_status_flags()
            self._update_power()

            # Update unit counts
            self.infantry_counts = self.read_and_store_inf_units_buildings(
                infantry_offsets, self.infantry_array_ptr, "infantry"
            )
            self.tank_counts = self.read_and_store_inf_units_buildings(
                tank_offsets, self.unit_array_ptr, "unit"
            )
            self.building_counts = self.read_and_store_inf_units_buildings(
                structure_offsets, self.building_array_ptr, "building"
            )
            self.aircraft_counts = self.read_and_store_inf_units_buildings(
                aircraft_offsets, self.aircraft_array_ptr, "aircraft"
            )

        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in update_dynamic_data for player {self.username.value}: {e}")
            traceback.print_exc()

    def _update_resources(self):
        """Updates player balance and spent credit by reading from memory."""
        self.balance = self._read_memory_offset(BALANCEOFFSET)
        self.spent_credit = self._read_memory_offset(CREDITSPENT_OFFSET)

    def _update_status_flags(self):
        """Updates player status flags (is_winner, is_loser) by reading from memory."""
        self.is_winner = bool(self._read_memory_offset(ISWINNEROFFSET, size=1))
        self.is_loser = bool(self._read_memory_offset(ISLOSEROFFSET, size=1))

    def _update_power(self):
        """Updates power output and drain, recalculating the net power."""
        self.power_output = self._read_memory_offset(POWEROUTPUTOFFSET)
        self.power_drain = self._read_memory_offset(POWERDRAINOFFSET)
        self.power = self.power_output - self.power_drain

    def _read_memory_offset(self, offset, size=4):
        """Reads memory at a specific offset and returns the integer value."""
        address = self.real_class_base + offset
        data = read_process_memory(self.process_handle, address, size)
        if data:
            return int.from_bytes(data, byteorder='little')
        return 0


# Supporting Classes and Functions
# ------------------------------------------------------------------------

class GameData:
    """Manages all players in the game and updates their data."""

    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def update_all_players(self):
        for player in self.players:
            player.update_dynamic_data()


def read_process_memory(process_handle, address, size):
    """Reads a block of memory from a process and returns the raw bytes."""
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    try:
        success = ctypes.windll.kernel32.ReadProcessMemory(
            process_handle, address, buffer, size, ctypes.byref(bytesRead)
        )
        if success:
            return buffer.raw
        else:
            error_code = ctypes.windll.kernel32.GetLastError()
            handle_memory_error(error_code)
            return None
    except Exception as e:
        logging.error(f"Exception in read_process_memory: {e}")
        raise ProcessExitedException("Process has exited.")


def handle_memory_error(error_code):
    """Handles errors related to reading process memory."""
    if error_code == 299:  # ERROR_PARTIAL_COPY
        logging.warning("Memory read incomplete. Game might still be loading.")
    elif error_code in (5, 6):  # ERROR_ACCESS_DENIED or ERROR_INVALID_HANDLE
        logging.error("Failed to read memory: Process might have exited.")
        raise ProcessExitedException("Process has exited.")
    else:
        logging.error(f"Failed to read memory: Error code {error_code}")
        raise ProcessExitedException("Process has exited.")


def detect_if_all_players_are_loaded(process_handle):
    """Detects if all players are fully loaded in memory before initialization."""
    try:
        fixedPoint = 0xa8b230
        classBaseArrayPtr = 0xa8022c
        return check_players_load_status(process_handle, fixedPoint, classBaseArrayPtr)
    except Exception as e:
        logging.error(f"Exception in detect_if_all_players_are_loaded: {e}")
        traceback.print_exc()
        return False


def check_players_load_status(process_handle, fixed_point, class_base_array_ptr):
    """Helper function to check if players are fully loaded by verifying memory values."""
    fixedPointData = read_process_memory(process_handle, fixed_point, 4)
    if fixedPointData is None:
        logging.error("Failed to read memory at fixedPoint.")
        return False

    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, class_base_array_ptr, 4)
    ).value
    classBasePlayer = ctypes.c_uint32.from_buffer_copy(fixedPointData).value + 1120 * 4

    for i in range(MAXPLAYERS):
        player_data = read_process_memory(process_handle, classBasePlayer, 4)
        if player_data:
            # Additional validation can go here
            return True
    return False


def initialize_players_after_loading(game_data, process_handle):
    """Initializes player objects after detecting that all players are loaded in memory."""
    game_data.players.clear()
    fixed_point = 0xa8b230
    class_base_array_ptr = 0xa8022c

    for i in range(MAXPLAYERS):
        player = Player(i + 1, process_handle, fixed_point)
        game_data.add_player(player)

    logging.info(f"Number of valid players initialized: {len(game_data.players)}")
    return len(game_data.players)
