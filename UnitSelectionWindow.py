import json
import logging
import os
from idlelib.debugger_r import frametable

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class UnitSelectionWindow(QMainWindow):
    def __init__(self, selected_units_dict, parent=None):
        super().__init__(parent)
        self.units_data = selected_units_dict['units']  # Load the units added so far
        self.selected_units = selected_units_dict['selected_units']  # Load selected units (if any)

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
            units = self.units_data.get(faction, {}).get(unit_type, [])

            # Only add the units that have been defined (otherwise keep the tab empty)
            row = 0
            col = 0
            for unit in units:
                if 'name' not in unit:
                    continue  # Skip invalid entries

                # Create a vertical layout for each unit (image acts as checkbox)
                unit_layout = QVBoxLayout()
                unit_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

                # Create image label and set it as clickable
                image_label = QLabel()
                image_path = unit.get('image', '')  # Ensure image path is available
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))

                # Set selection state and connect click event
                is_selected = self.is_unit_selected(faction, unit_type, unit['name'])
                self.update_image_selection(image_label, is_selected)

                # Add event handling to the label
                image_label.mousePressEvent = lambda event, f=faction, ut=unit_type, u=unit['name'], label=image_label: self.toggle_unit_selection(f, ut, u, label)

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
        """Check if a unit is already selected."""
        return self.selected_units.get(faction, {}).get(unit_type, {}).get(unit, False)

    def toggle_unit_selection(self, faction, unit_type, unit, label):
        """Toggle unit selection and update the appearance."""
        current_state = self.is_unit_selected(faction, unit_type, unit)
        new_state = not current_state

        logging.debug(f'{unit} changed state to {new_state}')

        # Update the selection status
        if faction not in self.selected_units:
            self.selected_units[faction] = {}
        if unit_type not in self.selected_units[faction]:
            self.selected_units[faction][unit_type] = {}

        self.selected_units[faction][unit_type][unit] = new_state

        # Update the image appearance
        self.update_image_selection(label, new_state)

    def update_image_selection(self, label, is_selected):
        """Update the image appearance based on whether it's selected or not."""
        pixmap = label.pixmap()
        if pixmap is not None:
            # Convert pixmap to QImage to modify brightness
            image = pixmap.toImage()

            # Modify the image to be lighter or darker
            for x in range(image.width()):
                for y in range(image.height()):
                    color = image.pixelColor(x, y)
                    if is_selected:
                        color = color.lighter(150)  # Make it lighter
                    else:
                        color = color.darker(150)  # Make it darker
                    image.setPixelColor(x, y, color)

            # Set the modified image back to the label
            label.setPixmap(QPixmap.fromImage(image))

