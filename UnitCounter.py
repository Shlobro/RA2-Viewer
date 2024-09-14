import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QFrame, QVBoxLayout
from CounterWidget import CounterWidget

from PySide6.QtWidgets import QVBoxLayout

class UnitWindow(QMainWindow):
    def __init__(self, player, player_count, hud_pos, unit_json_file="unit_selection.json"):
        super().__init__()
        self.player = player
        self.player_count = player_count
        self.unit_json_file = unit_json_file  # Reference to the JSON file for unit selection

        # Use the global size from hud_positions
        self.size = hud_pos.get('unit_counter_size', 100)  # Default size is 100 if not present

        # Get the initial position of the Unit HUD
        pos = self.get_default_position(player.index, 'unit', hud_pos)
        self.setGeometry(pos['x'], pos['y'], 120, 120)  # Set window size
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.make_hud_movable(hud_pos)

        unit_frame = QFrame(self)
        self.layout = QVBoxLayout(unit_frame)  # Use a vertical layout for stacking counters vertically
        self.layout.setSpacing(0)  # Ensure no space between widgets
        self.layout.setContentsMargins(0, 0, 0, 0)  # No margins around the edges

        # List to hold all the counters
        self.counters = []

        # Dynamically load selected units from JSON and create counters
        self.load_selected_units_and_create_counters()

        self.setCentralWidget(unit_frame)
        self.show()

    def load_selected_units_and_create_counters(self):
        """Load selected units from JSON and create CounterWidgets for them."""
        selected_units = self.load_selected_units_from_json()

        for faction, unit_types in selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, is_selected in units.items():
                    if is_selected:
                        # Determine where to fetch the unit count based on unit type
                        unit_count = self.get_unit_count(unit_type, unit_name)
                        unit_image_path = self.get_unit_image_path(faction, unit_type, unit_name)

                        # Create the CounterWidget for the selected unit
                        unit_counter = CounterWidget(unit_count, unit_image_path, self.player.color, self.size)
                        unit_counter.hide()
                        # Add the widget to the vertical layout
                        self.layout.addWidget(unit_counter)
                        self.counters.append(unit_counter)

    def get_unit_count(self, unit_type, unit_name):
        """Determine the unit type and retrieve the unit count from the relevant section."""

        if unit_name == 'Slave Miner Deployed' or unit_name == 'Slave miner undeployed':
            return self.player.infantry_counts.get('Slave Miner Deployed', 0) + self.player.infantry_counts.get('Slave miner undeployed', 0)
        elif unit_type == 'Infantry':
            return self.player.infantry_counts.get(unit_name, 0)
        elif unit_type == 'Tank' or 'Naval':
            return self.player.tank_counts.get(unit_name, 0)
        elif unit_type == 'Building':
            return self.player.building_counts.get(unit_name, 0)
        else:
            # Unknown unit type, return 0 as default
            return 0

    def get_unit_image_path(self, faction, unit_type, unit_name):
        """Fetch the image path for a given unit based on faction, unit type, and unit name."""
        with open(self.unit_json_file, 'r') as file:
            unit_data = json.load(file).get('units', {})

            # Get the list of units for the specified faction and unit type
            units_list = unit_data.get(faction, {}).get(unit_type, [])

            # Iterate over the units to find the one with the matching name
            for unit in units_list:
                if unit.get('name') == unit_name:
                    return unit.get('image', '')

            # Return an empty string if no match is found
            return ''

    def load_selected_units_from_json(self):
        """Load the selected units from the JSON file."""
        with open(self.unit_json_file, 'r') as file:
            return json.load(file).get('selected_units', {})

    def update_all_counters_size(self, new_size):
        """Update the size of all CounterWidgets in the UnitWindow."""
        self.size = new_size  # Update the stored size for the window
        for counter_widget in self.counters:
            counter_widget.setFixedSize(new_size, new_size)  # Resize each CounterWidget
            counter_widget.size = new_size  # Update size attribute
            counter_widget.update()  # Redraw the widget with the new size

        # Ensure the layout tightly packs the widgets after resizing
        self.layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.updateGeometry()  # Force the window to update its geometry

    def update_labels(self):
        """Loop through all counters and update the corresponding unit counts."""
        for counter_widget, (unit_name, unit_type) in zip(self.counters, self.get_unit_names_and_types()):
            # Get the latest unit count based on unit type
            unit_count = self.get_unit_count(unit_type, unit_name)

            # Update the counter widget with the latest unit count
            counter_widget.update_count(unit_count)
            if 0 < unit_count < 500:
                counter_widget.show()
            else:
                counter_widget.hide()

    def get_unit_count(self, unit_type, unit_name):
        """Determine the unit type and retrieve the unit count from the relevant section."""

        if unit_type == 'Infantry':
            return self.player.infantry_counts.get(unit_name, 0)
        elif unit_type == 'Tank':
            return self.player.tank_counts.get(unit_name, 0)
        elif unit_type == 'Building':
            return self.player.building_counts.get(unit_name, 0)
        else:
            # Unknown unit type, return 0 as default
            return 0

    def get_unit_names_and_types(self):
        """
        Return a list of (unit_name, unit_type) tuples for all the units in counters.
        """
        selected_units = self.load_selected_units_from_json()  # Reload the selected units
        unit_names_and_types = []

        for faction, unit_types in selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, is_selected in units.items():
                    if is_selected:
                        unit_names_and_types.append((unit_name, unit_type))

        return unit_names_and_types

    def make_hud_movable(self, hud_positions):
        self.offset = None

        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None:
                x = event.globalX() - self.offset.x()
                y = event.globalY() - self.offset.y()
                self.move(x, y)
                self.update_hud_position(hud_positions, self.player.index, 'unit', x, y)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def get_default_position(self, player_id, hud_type, hud_positions):
        player_id_str = str(player_id)
        player_count_str = str(self.player_count)

        # Check if player_count exists, if not, create it
        if player_count_str not in hud_positions:
            hud_positions[player_count_str] = {}

        # Check if player_id exists within player_count, if not, create it
        if player_id_str not in hud_positions[player_count_str]:
            hud_positions[player_count_str][player_id_str] = {}

        # Check if hud_type exists for the player, if not, create default position for it
        if hud_type not in hud_positions[player_count_str][player_id_str]:
            # Set default x and y positions
            default_position = {"x": 100 * player_id, "y": 100 * player_id}
            hud_positions[player_count_str][player_id_str][hud_type] = default_position
        else:
            # If hud_type exists, return the stored position
            default_position = hud_positions[player_count_str][player_id_str][hud_type]

        # Return the position (either the one from JSON or the default one we created)
        return default_position

    def update_hud_position(self, hud_positions, player_id, hud_type, x, y):
        player_id_str = str(player_id)

        # Ensure player count is correctly initialized in hud_positions
        if str(self.player_count) not in hud_positions:
            hud_positions[str(self.player_count)] = {}

        # Loop through all players to ensure each player has the complete structure
        for pid in range(1, self.player_count + 1):
            pid_str = str(pid)
            if pid_str not in hud_positions[str(self.player_count)]:
                # Initialize player entry with default positions
                hud_positions[str(self.player_count)][pid_str] = {
                    "x": 100 * pid,  # Default x position for player
                    "y": 100 * pid,  # Default y position for player
                    "unit": {  # Default unit position
                        "x": 100 * pid,
                        "y": 100 * pid
                    },
                    "resource": {  # Default resource position
                        "x": 100 * pid + 50,
                        "y": 100 * pid
                    }
                }

        # Now update the specific HUD for the current player
        hud_positions[str(self.player_count)][player_id_str][hud_type] = {"x": x, "y": y}
