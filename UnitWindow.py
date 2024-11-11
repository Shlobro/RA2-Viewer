# UnitWindow.py

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLayout

from CounterWidget import CounterWidgetImagesAndNumber, CounterWidgetNumberOnly, CounterWidgetImageOnly
from common import name_to_path, country_name_to_faction


class UnitWindowBase(QMainWindow):
    """Base class for unit display windows, managing layout, display settings, and unit counters."""

    def __init__(self, player, hud_pos, units_settings, spacing=0):
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units = units_settings.selected_units
        self.unit_info_by_name = units_settings.unit_info_by_name

        self.layout_type = hud_pos.positions.get('unit_layout', 'Vertical')
        self.size = self.get_default_size()
        self.show_unit_frames = hud_pos.positions.get('show_unit_frames', True)
        self.counters = {}
        self.spacing = spacing

        # Set window properties
        pos = self.get_default_position()
        self.setGeometry(pos['x'], pos['y'], 120, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        # Create the unit frame and layout
        self.unit_frame = QFrame(self)
        self.set_layout(self.layout_type, self.spacing)
        self.setCentralWidget(self.unit_frame)
        self.load_selected_units_and_create_counters()
        self.show()

    # Layout and Display Configuration
    # ------------------------------------------------------------------------

    def set_layout(self, layout_type, spacing):
        """Sets the layout type and spacing for the window."""
        self.layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
        self.layout.setSpacing(spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.unit_frame.setLayout(self.layout)

    def update_show_unit_frames(self, show_frame):
        """Updates visibility of unit frames in counters."""
        self.show_unit_frames = show_frame
        for counter_widget, _ in self.counters.values():
            counter_widget.update_show_frame(show_frame)

    def update_layout(self, layout_type, spacing=None):
        """Updates layout orientation and spacing if they differ from the current settings."""
        if self.layout_type != layout_type or (spacing is not None and self.layout.spacing() != spacing):
            self.layout_type = layout_type
            new_layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
            new_layout.setSpacing(spacing if spacing is not None else self.layout.spacing())
            new_layout.setContentsMargins(0, 0, 0, 0)

            for counter_widget, _ in self.counters.values():
                self.layout.removeWidget(counter_widget)
                new_layout.addWidget(counter_widget)

            QWidget().setLayout(self.layout)
            self.unit_frame.setLayout(new_layout)
            self.layout = new_layout
            self.updateGeometry()

    def update_spacing(self, new_spacing):
        """Updates the spacing between elements in the layout."""
        self.layout.setSpacing(new_spacing)
        self.layout.update()

    # Unit Counter Management
    # ------------------------------------------------------------------------

    def load_selected_units_and_create_counters(self):
        """Loads selected units and creates corresponding counter widgets."""
        for unit_name, unit_info in self.unit_info_by_name.items():
            if unit_info.get('selected', False):
                position = unit_info.get('position', -1)
                unit_type = unit_info.get('unit_type')
                counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
                counter_widget.hide()

                if self.layout.count() < position:
                    self.layout.addWidget(counter_widget)
                else:
                    self.layout.insertWidget(position, counter_widget)
                self.counters[unit_name] = (counter_widget, unit_type)

    def update_all_counters_size(self, new_size):
        """Updates the size of all counter widgets."""
        self.size = new_size
        for counter_widget, _ in self.counters.values():
            counter_widget.update_size(new_size)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.updateGeometry()

    def update_labels(self):
        """Refreshes unit counter labels based on the player's current unit counts."""
        player_faction = self.player.faction
        for unit_name, (counter_widget, unit_type) in self.counters.items():
            unit_count = self.get_unit_count(unit_type, unit_name)
            counter_widget.update_count(unit_count)

            unit_info = self.unit_info_by_name.get(unit_name, {})
            is_locked = unit_info.get('locked', False)
            unit_faction = unit_info.get('faction', None)
            is_selected = unit_info.get('selected', False)

            if (0 < unit_count < 500) or (is_locked and is_selected and (
                    unit_faction == player_faction or unit_name == "Blitz oil (psychic sensor)")):
                counter_widget.show()
            else:
                counter_widget.hide()
        self.update_all_counters_size(self.size)

    # Utility Methods for Unit Position and Type Handling
    # ------------------------------------------------------------------------

    def get_unit_count(self, unit_type, unit_name):
        """Retrieves the unit count from the player's data based on unit type."""
        if self.player is None:
            logging.warning("The game ended while retrieving unit counts.")
            return 0

        try:
            if unit_type == 'Infantry':
                return self.player.infantry_counts.get(unit_name, 0)
            elif unit_type in ('Tank', 'Naval'):
                return self.player.tank_counts.get(unit_name, 0)
            elif unit_type == 'Structure':
                if unit_name == 'Slave Miner Deployed' or unit_name == 'Slave miner undeployed':
                    return self.player.building_counts.get('Slave Miner Deployed', 0) + \
                        self.player.tank_counts.get('Slave miner undeployed', 0)
                elif unit_name == 'Allied AFC':
                    return self.player.building_counts.get('Allied AFC', 0) + \
                        self.player.building_counts.get('American AFC', 0)
                else:
                    return self.player.building_counts.get(unit_name, 0)
            else:
                return 0
        except AttributeError as e:
            logging.error(f"Error retrieving unit count: {e}")
            return 0

    # HUD Positioning and Movable HUD Window
    # ------------------------------------------------------------------------

    def make_hud_movable(self):
        """Enables the HUD window to be draggable."""
        self.offset = None

        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None:
                x = event.globalX() - self.offset.x()
                y = event.globalY() - self.offset.y()
                self.move(x, y)
                self.update_hud_position(x, y)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def get_default_position(self):
        """Returns the default position for the HUD window, based on player color and HUD type."""
        player_color_str = self.player.color_name
        hud_type = self.get_hud_type()

        if player_color_str not in self.hud_pos:
            self.hud_pos[player_color_str] = {}
        if hud_type not in self.hud_pos[player_color_str]:
            self.hud_pos[player_color_str][hud_type] = {"x": 100, "y": 100}

        default_position = self.hud_pos[player_color_str][hud_type]
        return {"x": int(default_position['x']), "y": int(default_position['y'])}

    def update_hud_position(self, x, y):
        """Updates the HUD position in the hud_pos dictionary."""
        player_color_str = self.player.color_name
        hud_type = self.get_hud_type()
        if player_color_str not in self.hud_pos:
            self.hud_pos[player_color_str] = {}
        self.hud_pos[player_color_str][hud_type] = {"x": x, "y": y}

    # Abstract Methods to be Implemented by Subclasses
    # ------------------------------------------------------------------------

    def get_default_size(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def get_hud_type(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        raise NotImplementedError("Subclasses should implement this method.")


# Specific Unit Window Classes
# ------------------------------------------------------------------------

class UnitWindowWithImages(UnitWindowBase):
    """Unit window displaying both images and numbers for each unit."""

    def get_default_size(self):
        return self.hud_pos.get('unit_counter_size', 100)

    def get_hud_type(self):
        return 'unit_counter_combined'

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        unit_image_path = name_to_path(unit_name)
        return CounterWidgetImagesAndNumber(
            count=unit_count,
            image_path=unit_image_path,
            color=self.player.color,
            size=self.size,
            show_frame=self.show_unit_frames
        )


class UnitWindowImagesOnly(UnitWindowBase):
    """Unit window displaying only images for each unit."""

    def get_default_size(self):
        return self.hud_pos.get('image_size', 75)

    def get_hud_type(self):
        return 'unit_counter_images'

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        unit_image_path = name_to_path(unit_name)
        return CounterWidgetImageOnly(
            image_path=unit_image_path,
            color=self.player.color,
            size=self.size,
            show_frame=self.show_unit_frames
        )


class UnitWindowNumbersOnly(UnitWindowBase):
    """Unit window displaying only numbers for each unit."""

    def __init__(self, player, hud_pos, units_settings):
        self.distance_between_numbers = hud_pos.get('distance_between_numbers', 0)
        super().__init__(player, hud_pos, units_settings, spacing=self.distance_between_numbers)

    def get_default_size(self):
        return self.hud_pos.get('number_size', 75)

    def get_hud_type(self):
        return 'unit_counter_numbers'

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        return CounterWidgetNumberOnly(
            count=unit_count,
            color=self.player.color,
            size=self.size
        )

    def update_spacing(self, new_spacing):
        self.layout.setSpacing(new_spacing)
        self.updateGeometry()
