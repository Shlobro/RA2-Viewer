import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QFrame, QVBoxLayout, QWidget, QHBoxLayout
from CounterWidget import CounterWidget
import logging
from PySide6.QtWidgets import QVBoxLayout
from common import (name_to_path)


class UnitWindow(QMainWindow):
    def __init__(self, player, player_count, hud_pos, selected_units_dict):
        super().__init__()
        self.player = player
        self.player_count = player_count
        self.selected_units_dict = selected_units_dict
        self.selected_units = selected_units_dict['selected_units']
        self.layout_type = hud_pos.get('unit_layout', 'Vertical')  # Default to Vertical layout
        self.size = hud_pos.get('unit_counter_size', 100)
        self.show_unit_frames = hud_pos.get('show_unit_frames', True)  # Get the setting


        # Set window geometry and flags
        # Example in UnitWindow or ResourceWindow instantiation
        pos = self.get_default_position(self.player.color_name, 'unit_counter', hud_pos)
        self.setGeometry(pos['x'], pos['y'], 120, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.make_hud_movable(hud_pos)

        # Create the unit frame and apply the correct layout
        self.unit_frame = QFrame(self)
        self.set_layout(self.layout_type)

        # List to hold all the counters
        self.counters = {}
        self.load_selected_units_and_create_counters()

        self.setCentralWidget(self.unit_frame)
        self.show()

    def set_layout(self, layout_type):
        """Set the layout based on the provided layout type."""
        self.layout = QVBoxLayout(self.unit_frame) if layout_type == 'Vertical' else QHBoxLayout(self.unit_frame)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def update_show_unit_frames(self, show_frame):
        """Update the show_frame setting for all CounterWidgets."""
        self.show_unit_frames = show_frame  # Update the stored setting
        for _, (counter_widget, _) in self.counters.items():
            counter_widget.update_show_frame(show_frame)

    def update_layout(self, layout_type):
        """Update the layout dynamically without deleting widgets."""
        if self.layout_type != layout_type:
            self.layout_type = layout_type

            # Create a new layout without resetting widgets
            new_layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
            new_layout.setSpacing(0)
            new_layout.setContentsMargins(0, 0, 0, 0)

            # Move existing widgets to the new layout
            for unit_name, (counter_widget, unit_type) in self.counters.items():
                self.layout.removeWidget(counter_widget)  # Remove from the old layout
                new_layout.addWidget(counter_widget)  # Add to the new layout

            # Replace the old layout with the new one
            QWidget().setLayout(self.layout)  # Detach the old layout from the frame
            self.unit_frame.setLayout(new_layout)  # Apply the new layout to the unit frame
            self.layout = new_layout  # Update the reference to the new layout
            self.updateGeometry()  # Force the window to update its geometry

    def load_selected_units_and_create_counters(self):
        """Load selected units from JSON and create CounterWidgets for them."""
        for faction, unit_types in self.selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, is_selected in units.items():
                    if is_selected:
                        unit_count = self.get_unit_count(unit_type, unit_name)
                        unit_image_path = name_to_path(unit_name)

                        unit_counter = CounterWidget(
                            unit_count,
                            unit_image_path,
                            self.player.color,
                            self.size,
                            show_frame=self.show_unit_frames  # Pass the setting
                        )
                        unit_counter.hide()

                        # Add the widget to the current layout
                        self.layout.addWidget(unit_counter)
                        self.counters[unit_name] = (unit_counter, unit_type)

    def update_selected_widgets(self, faction, unit_type, unit_name, state):
        if state:
            unit_count = self.get_unit_count(unit_type, unit_name)
            unit_image_path = name_to_path(unit_name)

            unit_counter = CounterWidget(unit_count, unit_image_path, self.player.color, self.size)
            unit_counter.hide()

            # Add the widget to the current layout
            self.layout.addWidget(unit_counter)
            self.counters[unit_name] = (unit_counter, unit_type)
        else:
            counter_widget, _ = self.counters[unit_name]
            self.layout.removeWidget(counter_widget)
            counter_widget.deleteLater()
            del self.counters[unit_name]

    def update_all_counters_size(self, new_size):
        """Update the size of all CounterWidgets in the UnitWindow."""
        self.size = new_size  # Update the stored size for the window
        for _, (counter_widget, _) in self.counters.items():
            counter_widget.update_size(new_size)  # Resize each CounterWidget dynamically

        # Ensure the layout tightly packs the widgets after resizing
        self.layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.updateGeometry()  # Force the window to update its geometry

    def update_labels(self):
        """Loop through all counters and update the corresponding unit counts."""
        logging.debug("updating all unit counters")
        for unit_name, (counter_widget, unit_type) in self.counters.items():
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
        if self.player is None:
            logging.warning("The game ended while retrieving unit counts.")
            return 0  # Return 0 or any other default value

        try:
            if unit_type == 'Infantry':
                return self.player.infantry_counts.get(unit_name, 0)
            elif unit_type == 'Tank' or unit_type == 'Naval':
                return self.player.tank_counts.get(unit_name, 0)
            elif unit_type == 'Structure':
                if unit_name == 'Slave Miner Deployed' or unit_name == 'Slave miner undeployed':
                    return self.player.building_counts.get('Slave Miner Deployed', 0) + self.player.tank_counts.get(
                        'Slave miner undeployed', 0)
                elif unit_name == 'Allied AFC':
                    return self.player.building_counts.get('Allied AFC', 0) + self.player.building_counts.get(
                        'American AFC', 0)
                else:
                    return self.player.building_counts.get(unit_name, 0)
            else:
                # Unknown unit type, return 0 as default
                return 0
        except AttributeError as e:
            logging.error(f"Error retrieving unit count: {e}")
            logging.warning("Game likely ended while retrieving unit counts.")
            return 0  # Return a default value to avoid further errors

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
                self.update_hud_position(hud_positions, self.player.color_name, 'unit_counter', x, y)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def get_default_position(self, player_color, hud_type, hud_positions):
        player_color_str = player_color  # Use the color as the key

        # Ensure the player's color section exists in the hud_positions
        if player_color_str not in hud_positions:
            hud_positions[player_color_str] = {}

        # Check if hud_type exists for the player, if not, create default position for it
        if hud_type not in hud_positions[player_color_str]:
            # Set default x and y positions
            default_position = {"x": 100, "y": 100}
            hud_positions[player_color_str][hud_type] = default_position
        else:
            # If hud_type exists, return the stored position
            default_position = hud_positions[player_color_str][hud_type]

        # Ensure x and y are integers before returning
        default_position['x'] = int(default_position['x'])
        default_position['y'] = int(default_position['y'])

        return default_position

    def update_hud_position(self, hud_positions, player_color, hud_type, x, y):
        player_color_str = player_color  # Use the color as the key

        # Ensure the player's section exists in hud_positions
        if player_color_str not in hud_positions:
            hud_positions[player_color_str] = {}

        # Update the specific HUD position for this player and type
        hud_positions[player_color_str][hud_type] = {"x": x, "y": y}

