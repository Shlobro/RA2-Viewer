import json
import logging
import os
from idlelib.debugger_r import frametable

from PySide6.QtGui import QPixmap, QImage, QAction, QPainter
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QMenu
from PySide6.QtCore import Qt

from common import (names, name_to_path)


class UnitSelectionWindow(QMainWindow):
    def __init__(self, selected_units_dict, hud_windows, parent=None):
        super().__init__(parent)
        self.hud_windows = hud_windows

        # Ensure 'selected_units' key exists in selected_units_dict
        if 'selected_units' not in selected_units_dict:
            selected_units_dict['selected_units'] = {}
        self.units_data = selected_units_dict['selected_units']

        # Migrate units data to new format if necessary
        self.migrate_units_data()

        self.setWindowTitle("Unit Selection")
        self.setGeometry(200, 200, 400, 300)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Create tabs for factions
        self.tab_widget = QTabWidget()
        self.create_faction_tabs()

        # Layout setup
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.tab_widget)

    def create_faction_tabs(self):
        factions = ['Allied', 'Soviet', 'Yuri']
        for faction in factions:
            faction_tab = QWidget()
            faction_layout = QVBoxLayout(faction_tab)

            # Create sub-tabs (Infantry, Structure, Tank, Naval, Aircraft)
            sub_tab_widget = QTabWidget()
            self.create_sub_tabs(faction, sub_tab_widget)

            faction_layout.addWidget(sub_tab_widget)
            self.tab_widget.addTab(faction_tab, faction)

    def create_sub_tabs(self, faction, sub_tab_widget):
        """Create sub-tabs and populate them with units if available."""
        unit_types = ['Infantry', 'Structure', 'Tank', 'Naval', 'Aircraft']
        for unit_type in unit_types:
            sub_tab = QWidget()
            sub_layout = QGridLayout(sub_tab)  # Use QGridLayout for grid arrangement
            sub_layout.setAlignment(Qt.AlignTop)  # Align everything at the top of the tab

            # Check if there are any units defined for this faction and unit type
            units = names[faction][unit_type]

            # Only add the units that have been defined (otherwise keep the tab empty)
            row = 0
            col = 0
            for unit in units:
                # Create a vertical layout for each unit (image acts as checkbox)
                unit_layout = QVBoxLayout()
                unit_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

                # Create image label and set it as clickable
                image_label = QLabel()
                image_path = name_to_path(unit)  # Ensure image path is available
                image_label.setProperty("image_path", image_path)  # Store the image path
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))

                # Set selection state and connect click event
                is_selected = self.is_unit_selected(faction, unit_type, unit)
                is_locked = self.is_unit_locked(faction, unit_type, unit)
                self.update_image_selection(image_label, is_selected, is_locked)

                # Add event handling to the label
                image_label.mousePressEvent = lambda event, f=faction, ut=unit_type, u=unit, label=image_label: self.unit_image_mousePressEvent(event, f, ut, u, label)


                # Add the image label to the unit's layout
                unit_layout.addWidget(image_label, alignment=Qt.AlignHCenter)

                # Add the unit layout to the grid layout
                sub_layout.addLayout(unit_layout, row, col)

                # Update row and column for the grid (e.g., 3 columns per row)
                col += 1
                if col >= 3:  # You can adjust the number of columns here
                    col = 0
                    row += 1

            sub_tab_widget.addTab(sub_tab, unit_type)

    def is_unit_selected(self, faction, unit_type, unit):
        unit_info = self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {})

        # Check if unit_info is a boolean (old format)
        if isinstance(unit_info, bool):
            # Convert to new format
            unit_info = {'selected': unit_info, 'locked': False}
            self.units_data[faction][unit_type][unit] = unit_info

        return unit_info.get('selected', False)

    def is_unit_locked(self, faction, unit_type, unit):
        unit_info = self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {})

        # Check if unit_info is a boolean (old format)
        if isinstance(unit_info, bool):
            # Convert to new format
            unit_info = {'selected': unit_info, 'locked': False}
            self.units_data[faction][unit_type][unit] = unit_info

        return unit_info.get('locked', False)

    def migrate_units_data(self):
        for faction, unit_types in self.units_data.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    if isinstance(unit_info, bool):
                        # Convert to new format
                        self.units_data[faction][unit_type][unit_name] = {'selected': unit_info, 'locked': False}

    def unit_image_mousePressEvent(self, event, faction, unit_type, unit_name, label):
        if event.button() == Qt.LeftButton:
            # Toggle selection
            self.toggle_unit_selection(faction, unit_type, unit_name, label)
        elif event.button() == Qt.RightButton:
            # Show context menu
            self.show_unit_context_menu(event, faction, unit_type, unit_name, label)

    def show_unit_context_menu(self, event, faction, unit_type, unit_name, label):
        menu = QMenu(self)
        is_locked = self.is_unit_locked(faction, unit_type, unit_name)
        action_text = "Unlock Unit" if is_locked else "Lock Unit"
        lock_action = QAction(action_text, self)
        lock_action.triggered.connect(lambda: self.toggle_unit_lock(faction, unit_type, unit_name, label))
        menu.addAction(lock_action)
        menu.exec(event.globalPos())

    def update_image_selection(self, label, is_selected, is_locked):
        # Get the image path from the label's property
        image_path = label.property("image_path")
        if not image_path:
            return
        # Load the original pixmap
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
        # Modify the pixmap
        image = pixmap.toImage()
        # Modify brightness based on selection
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y)
                color = color.lighter(150) if is_selected else color.darker(150)
                image.setPixelColor(x, y, color)
        # Overlay a lock icon if locked
        if is_locked:
            painter = QPainter()
            painter.begin(image)
            lock_icon = QPixmap('lock_icon.png')  # Ensure this path is correct
            lock_icon = lock_icon.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, lock_icon)
            painter.end()
        label.setPixmap(QPixmap.fromImage(image))

    def toggle_unit_lock(self, faction, unit_type, unit_name, label):
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        current_state = unit_info.get('locked', False)
        new_state = not current_state
        unit_info['locked'] = new_state
        logging.debug(f'{unit_name} lock state changed to {new_state}')
        # Update the image appearance
        self.update_image_selection(label, self.is_unit_selected(faction, unit_type, unit_name), new_state)
        # Update the unit counters
        for unit_counter, _ in self.hud_windows:
            if isinstance(unit_counter, tuple):
                for uc in unit_counter:
                    uc.update_locked_widgets(faction, unit_type, unit_name, new_state)
            else:
                unit_counter.update_locked_widgets(faction, unit_type, unit_name, new_state)

    def toggle_unit_selection(self, faction, unit_type, unit_name, label):
        """Toggle unit selection and update the appearance."""
        current_state = self.is_unit_selected(faction, unit_type, unit_name)
        new_state = not current_state

        logging.debug(f'{unit_name} selection state changed to {new_state}')

        # Update the selection status
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        unit_info['selected'] = new_state

        # Update the image appearance
        is_locked = self.is_unit_locked(faction, unit_type, unit_name)
        self.update_image_selection(label, new_state, is_locked)

        # Update the widget
        for unit_counter, _ in self.hud_windows:
            if isinstance(unit_counter, tuple):
                for uc in unit_counter:
                    uc.update_selected_widgets(faction, unit_type, unit_name, new_state)
            else:
                unit_counter.update_selected_widgets(faction, unit_type, unit_name, new_state)


