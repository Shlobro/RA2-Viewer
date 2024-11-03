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

class ProcessExitedException(Exception):
    """Custom exception to indicate that the game process has exited."""
    pass


class Player:
    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.process_handle = process_handle
        self.real_class_base = real_class_base

        self.username = ctypes.create_unicode_buffer(0x20)
        self.color = ""
        self.color_name = ''
        self.country_name = ctypes.create_string_buffer(0x40)

        self.faction = 'Unknown'  # Add this attribute

        self.is_winner = False
        self.is_loser = False

        self.balance = 0
        self.spent_credit = 0
        self.power_output = 0
        self.power_drain = 0
        self.power = self.power_output - self.power_drain

        # Store the counts of units, infantry, and buildings
        self.infantry_counts = {}
        self.tank_counts = {}
        self.building_counts = {}
        self.aircraft_counts = {}

        # Initialize pointers for arrays
        self.unit_array_ptr = None
        self.building_array_ptr = None
        self.infantry_array_ptr = None
        self.aircraft_array_ptr = None

        # Test case addresses
        self.test_addresses = {
            "infantry": self.real_class_base + 0x0b30,
            "unit": self.real_class_base + 0x1338,
            "building": self.real_class_base + 0x1b40,
            "aircraft": self.real_class_base + 0x328
        }

        # Initialize the pointers by reading memory
        self.initialize_pointers()

    def initialize_pointers(self):
        """ Initialize the pointers for the arrays of units, buildings, and infantry. """
        # Step 1: Read the pointer to the units array (use the TANKOFFSET)
        tank_offset = TANKOFFSET
        tank_ptr_address = self.real_class_base + tank_offset
        tank_ptr_data = read_process_memory(self.process_handle, tank_ptr_address, 4)
        if tank_ptr_data:
            self.unit_array_ptr = ctypes.c_uint32.from_buffer_copy(tank_ptr_data).value
        logging.debug(f"Initialized unit array pointer: {self.unit_array_ptr}")

        # Step 2: Read the pointer to the buildings array (use the BUILDINGOFFSET)
        building_offset = BUILDINGOFFSET
        building_ptr_address = self.real_class_base + building_offset
        building_ptr_data = read_process_memory(self.process_handle, building_ptr_address, 4)
        if building_ptr_data:
            self.building_array_ptr = ctypes.c_uint32.from_buffer_copy(building_ptr_data).value
        logging.debug(f"Initialized building array pointer: {self.building_array_ptr}")

        # Step 3: Read the pointer to the infantry array (use the INFOFFSET)
        infantry_offset = INFOFFSET
        infantry_ptr_address = self.real_class_base + infantry_offset
        infantry_ptr_data = read_process_memory(self.process_handle, infantry_ptr_address, 4)
        if infantry_ptr_data:
            self.infantry_array_ptr = ctypes.c_uint32.from_buffer_copy(infantry_ptr_data).value
        logging.debug(f"Initialized infantry array pointer: {self.infantry_array_ptr}")

        # Step 4: Read the pointer to the aircraft array
        aircraft_offset = AIRCRAFTOFFSET
        aircraft_ptr_address = self.real_class_base + aircraft_offset
        aircraft_ptr_data = read_process_memory(self.process_handle, aircraft_ptr_address, 4)
        if aircraft_ptr_data:
            self.aircraft_array_ptr = ctypes.c_uint32.from_buffer_copy(aircraft_ptr_data).value
        logging.debug(f"Initialized aircraft array pointer: {self.aircraft_array_ptr}")

    def read_and_store_inf_units_buildings(self, category_dict, array_ptr, count_type):
        try:
            """ Helper method to read memory and store values for infantry, tanks, or buildings. """
            if array_ptr is None:
                return {}

            counts = {}
            for offset, name in category_dict.items():
                specific_address = array_ptr + offset
                test_address = self.test_addresses[count_type] + offset

                count_data = read_process_memory(self.process_handle, specific_address, 4)
                test_data = read_process_memory(self.process_handle, test_address, 4)

                if count_data and test_data:  # Check if both are not None
                    count = int.from_bytes(count_data, byteorder='little')
                    test = int.from_bytes(test_data, byteorder='little')
                    # // TODO this if statement is dumb. why won't the test value work for the oils?
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
            raise  # Propagate the exception to be handled by the caller
        except Exception as e:
            logging.error(f"Exception in read_and_store_inf_units_buildings for player {self.username.value}: {e}")
            traceback.print_exc()

    def write_oil_count_to_file(self, oil_count):
        try:
            # Construct the filename based on the player's color
            filename = f"{self.color_name}_oil_count.txt"
            # Open the file in write mode (this will create the file if it doesn't exist)
            with open(filename, 'w') as file:
                file.write(str(oil_count))
            logging.debug(f"Wrote oil count {oil_count} to file {filename}")
        except Exception as e:
            logging.error(f"Failed to write oil count to file: {e}")

    def update_dynamic_data(self):
        try:
            logging.debug(f"Updating dynamic data for player {self.index}")

            # Balance
            balance_ptr = self.real_class_base + BALANCEOFFSET
            balance_data = read_process_memory(self.process_handle, balance_ptr, 4)
            if balance_data:
                self.balance = ctypes.c_uint32.from_buffer_copy(balance_data).value

            # Spent credit
            spent_credit_ptr = self.real_class_base + CREDITSPENT_OFFSET
            spent_credit_data = read_process_memory(self.process_handle, spent_credit_ptr, 4)
            if spent_credit_data:
                self.spent_credit = ctypes.c_uint32.from_buffer_copy(spent_credit_data).value

            # IsWinner
            is_winner_ptr = self.real_class_base + ISWINNEROFFSET
            is_winner_data = read_process_memory(self.process_handle, is_winner_ptr, 1)
            if is_winner_data:
                self.is_winner = bool(ctypes.c_uint8.from_buffer_copy(is_winner_data).value)

            # IsLoser
            is_loser_ptr = self.real_class_base + ISLOSEROFFSET
            is_loser_data = read_process_memory(self.process_handle, is_loser_ptr, 1)
            if is_loser_data:
                self.is_loser = bool(ctypes.c_uint8.from_buffer_copy(is_loser_data).value)

            # Power output
            power_output_ptr = self.real_class_base + POWEROUTPUTOFFSET
            power_output_data = read_process_memory(self.process_handle, power_output_ptr, 4)
            if power_output_data:
                self.power_output = ctypes.c_uint32.from_buffer_copy(power_output_data).value

            # Power drain
            power_drain_ptr = self.real_class_base + POWERDRAINOFFSET
            power_drain_data = read_process_memory(self.process_handle, power_drain_ptr, 4)
            if power_drain_data:
                self.power_drain = ctypes.c_uint32.from_buffer_copy(power_drain_data).value

            self.power = self.power_output - self.power_drain

            # Update infantry, tank, building, and aircraft counts
            if self.infantry_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.infantry_counts = self.read_and_store_inf_units_buildings(
                    infantry_offsets, self.infantry_array_ptr, "infantry"
                )

            if self.unit_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.tank_counts = self.read_and_store_inf_units_buildings(
                    tank_offsets, self.unit_array_ptr, "unit"
                )

            if self.building_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.building_counts = self.read_and_store_inf_units_buildings(
                    structure_offsets, self.building_array_ptr, "building"
                )

            if self.aircraft_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.aircraft_counts = self.read_and_store_inf_units_buildings(
                    aircraft_offsets, self.aircraft_array_ptr, "aircraft"
                )

        except ProcessExitedException:
            raise  # Propagate the exception to be handled by the caller
        except Exception as e:
            logging.error(f"Exception in update_dynamic_data for player {self.username.value}: {e}")
            traceback.print_exc()

class GameData:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def update_all_players(self):
        for player in self.players:
            player.update_dynamic_data()

def read_process_memory(process_handle, address, size):
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
            if error_code == 299:  # ERROR_PARTIAL_COPY
                logging.warning("Memory read incomplete. Game might still be loading.")
                return None
            elif error_code in (5, 6):  # ERROR_ACCESS_DENIED or ERROR_INVALID_HANDLE
                logging.error("Failed to read memory: Process might have exited.")
                raise ProcessExitedException("Process has exited.")
            else:
                logging.error(f"Failed to read memory: Error code {error_code}")
                raise ProcessExitedException("Process has exited.")
    except Exception as e:
        logging.error(f"Exception in read_process_memory: {e}")
        raise ProcessExitedException("Process has exited.")

# Define the mapping of color scheme values to actual color names
COLOR_SCHEME_MAPPING = {
    3: QColor("yellow"),
    5: QColor("white"),
    7: QColor("gray"),
    11: QColor("red"),
    13: QColor("orange"),
    15: QColor("pink"),
    17: QColor("purple"),
    21: QColor("blue"),
    25: QColor("cyan"),
    29: QColor("green"),
}

def get_color(color_scheme):
    """Returns a QColor object based on the color scheme value."""
    return COLOR_SCHEME_MAPPING.get(color_scheme, QColor("black"))

def get_color_name(color_scheme):
    """Returns a color name based on the color scheme value."""
    return COLOR_NAME_MAPPING.get(color_scheme, "white")

def detect_if_all_players_are_loaded(process_handle):
    """Wait for players to be fully loaded before proceeding with initialization."""
    try:
        fixedPoint = 0xa8b230
        classBaseArrayPtr = 0xa8022c

        fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
        if fixedPointData is None:
            logging.error("Failed to read memory at fixedPoint.")
            return False

        fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
        classBaseArray = ctypes.c_uint32.from_buffer_copy(
            read_process_memory(process_handle, classBaseArrayPtr, 4)
        ).value
        classBasePlayer = fixedPointValue + 1120 * 4

        for i in range(MAXPLAYERS):
            player_data = read_process_memory(process_handle, classBasePlayer, 4)
            classBasePlayer += 4
            if player_data is None:
                logging.warning(f"Skipping Player {i} due to incomplete memory read.")
                continue

            classBasePtr = ctypes.c_uint32.from_buffer_copy(player_data).value
            if classBasePtr == INVALIDCLASS:
                logging.info(f"Skipping Player {i} as not fully initialized yet.")
                continue

            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)
            if realClassBaseData is None:
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value

            loaded = 0
            right_values = {0x551c: 66, 0x5778: 0, 0x57ac: 90}
            for offset, value in right_values.items():
                ptr = realClassBase + offset
                data = read_process_memory(process_handle, ptr, 4)
                if data and int.from_bytes(data, byteorder='little') == value:
                    loaded += 1

            if loaded >= 2:
                logging.info("Players loaded. Proceeding with players initialization.")
                return True
        return False

    except Exception as e:
        logging.error(f"Exception in detect_if_all_players_are_loaded: {e}")
        traceback.print_exc()
        return False

def initialize_players_after_loading(game_data, process_handle):
    """Initialize all players after detecting they are loaded."""
    game_data.players.clear()

    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointData is None:
        logging.error("Failed to read memory at fixedPoint.")
        return 0

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, classBaseArrayPtr, 4)
    ).value
    classbasearray = fixedPointValue + 1120 * 4
    valid_player_count = 0

    for i in range(MAXPLAYERS):
        memory_data = read_process_memory(process_handle, classbasearray, 4)
        classbasearray += 4

        if memory_data is None:
            logging.warning(f"Skipping player {i} due to incomplete memory read.")
            continue

        classBasePtr = ctypes.c_uint32.from_buffer_copy(memory_data).value
        if classBasePtr != INVALIDCLASS:
            valid_player_count += 1
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)

            if realClassBaseData is None:
                logging.warning(f"Skipping player {i} due to incomplete real class base read.")
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value
            player = Player(i + 1, process_handle, realClassBase)

            # Set the color
            colorPtr = realClassBase + COLORSCHEMEOFFSET
            color_data = read_process_memory(process_handle, colorPtr, 4)
            if color_data is None:
                logging.warning(f"Skipping color assignment for player {i} due to incomplete memory read.")
                continue
            color_scheme_value = ctypes.c_uint32.from_buffer_copy(color_data).value
            player.color = get_color(color_scheme_value)
            player.color_name = get_color_name(color_scheme_value)
            logging.info(f"Player {i} color: {player.color_name}")

            # Set the country name
            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBaseData = read_process_memory(process_handle, houseTypeClassBasePtr, 4)
            if houseTypeClassBaseData is None:
                logging.warning(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            houseTypeClassBase = ctypes.c_uint32.from_buffer_copy(houseTypeClassBaseData).value
            countryNamePtr = houseTypeClassBase + COUNTRYSTRINGOFFSET
            country_data = read_process_memory(process_handle, countryNamePtr, 25)
            if country_data is None:
                logging.warning(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.country_name, country_data, 25)
            country_name_str = player.country_name.value.decode('utf-8').strip('\x00')
            logging.info(f"Player {i} country name: {country_name_str}")

            # Set the faction based on the country name
            player.faction = country_name_to_faction(country_name_str)
            logging.info(f"Player {i} faction: {player.faction}")

            # Set the username
            userNamePtr = realClassBase + USERNAMEOFFSET
            username_data = read_process_memory(process_handle, userNamePtr, 0x20)
            if username_data is None:
                logging.warning(f"Skipping username assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.username, username_data, 0x20)
            logging.info(f"Player {i} name: {player.username.value}")

            game_data.add_player(player)

    logging.info(f"Number of valid players: {valid_player_count}")
    return valid_player_count
