# UnitSelectionWindow.py
import logging
from PySide6.QtGui import QPixmap, QAction, QPainter, QFont
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QLabel, QMenu, QInputDialog
from PySide6.QtCore import Qt

from common import name_to_path, factions, unit_types


class UnitSelectionWindow(QMainWindow):
    """A window for selecting units across factions and types, with options to lock, position, and visually update units."""

    def __init__(self, unit_data, hud_windows, parent=None):
        super().__init__(parent)
        self.hud_windows = hud_windows
        self.units_data = unit_data.selected_units

        self.setWindowTitle("Unit Selection")
        self.setGeometry(200, 200, 400, 300)

        # Main widget and layout
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Tab widget for factions
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs for each faction
        self.create_faction_tabs()

    def create_faction_tabs(self):
        """Creates main tabs for each faction, and adds sub-tabs by unit type."""
        for faction in factions:
            faction_tab = QWidget()
            faction_layout = QVBoxLayout(faction_tab)

            sub_tab_widget = QTabWidget()
            self.create_sub_tabs(faction, sub_tab_widget)

            faction_layout.addWidget(sub_tab_widget)
            self.tab_widget.addTab(faction_tab, faction)

    def create_sub_tabs(self, faction, sub_tab_widget):
        """Creates sub-tabs for each unit type within a faction, displaying unit options."""
        for unit_type in unit_types:
            sub_tab = QWidget()
            sub_layout = QGridLayout(sub_tab)
            sub_layout.setAlignment(Qt.AlignTop)

            units = list(self.units_data.get(faction, {}).get(unit_type, {}).keys())
            row, col = 0, 0
            for unit in units:
                unit_layout = self.create_unit_layout(faction, unit_type, unit)
                sub_layout.addLayout(unit_layout, row, col)

                col += 1
                if col >= 3:
                    col = 0
                    row += 1

            sub_tab_widget.addTab(sub_tab, unit_type)

    def create_unit_layout(self, faction, unit_type, unit):
        """Creates a layout for each unit option with an image label."""
        unit_layout = QVBoxLayout()
        unit_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Set up the image label with selection and event handling
        image_label = QLabel()
        image_label.setProperty("image_path", name_to_path(unit))
        pixmap = QPixmap(image_label.property("image_path"))
        if not pixmap.isNull():
            image_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))

        # Update initial selection and lock state, and add click handling
        is_selected = self.is_unit_selected(faction, unit_type, unit)
        is_locked = self.is_unit_locked(faction, unit_type, unit)
        position = self.get_unit_position(faction, unit_type, unit)
        self.update_image_selection(image_label, is_selected, is_locked, position)

        image_label.mousePressEvent = lambda event, f=faction, ut=unit_type, u=unit,
                                             label=image_label: self.unit_image_mousePressEvent(event, f, ut, u, label)
        unit_layout.addWidget(image_label, alignment=Qt.AlignHCenter)
        return unit_layout

    # Helper Methods for Unit Properties
    # ------------------------------------------------------------------------

    def is_unit_selected(self, faction, unit_type, unit):
        return self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {}).get('selected', False)

    def get_unit_position(self, faction, unit_type, unit):
        return self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {}).get('position', -1)

    def is_unit_locked(self, faction, unit_type, unit):
        return self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {}).get('locked', False)

    # Event Handling for Unit Selection
    # ------------------------------------------------------------------------

    def unit_image_mousePressEvent(self, event, faction, unit_type, unit_name, label):
        """Handles left-click selection and right-click context menu for units."""
        if event.button() == Qt.LeftButton:
            self.toggle_unit_selection(faction, unit_type, unit_name, label)
        elif event.button() == Qt.RightButton:
            self.show_unit_context_menu(event, faction, unit_type, unit_name, label)

    def show_unit_context_menu(self, event, faction, unit_type, unit_name, label):
        """Displays a context menu for locking and setting unit position."""
        menu = QMenu(self)

        # Toggle lock/unlock action
        is_locked = self.is_unit_locked(faction, unit_type, unit_name)
        lock_action = QAction("Unlock Unit" if is_locked else "Lock Unit", self)
        lock_action.triggered.connect(lambda: self.toggle_unit_lock(faction, unit_type, unit_name, label))
        menu.addAction(lock_action)

        # Set position action
        position_action = QAction("Set Position", self)
        position_action.triggered.connect(lambda: self.set_position(faction, unit_type, unit_name, label))
        menu.addAction(position_action)

        menu.exec(event.globalPos())

    def set_position(self, faction, unit_type, unit_name, label):
        """Prompt the user to set a position for the unit, updating HUDs as needed."""
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        position, ok = QInputDialog.getInt(self, f"Set Position for {unit_name}", "Enter a positive position:",
                                           unit_info.get('position', -1))
        if ok:
            self.handle_position_change(position, faction, unit_type, unit_name, label)

    def handle_position_change(self, position, faction, unit_type, unit_name, label):
        """Updates unit position and reflects changes in HUD widgets."""
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        unit_info['position'] = position
        self.update_image_selection(label, self.is_unit_selected(faction, unit_type, unit_name),
                                    self.is_unit_locked(faction, unit_type, unit_name), position)

        # Update HUD widgets
        for unit_counter, _ in self.hud_windows:
            if isinstance(unit_counter, tuple):
                for uc in unit_counter:
                    uc.update_position_widgets(faction, unit_type, unit_name)
            else:
                unit_counter.update_position_widgets(faction, unit_type, unit_name)

    def toggle_unit_selection(self, faction, unit_type, unit_name, label):
        """Toggle unit selection and update the appearance."""
        current_state = self.is_unit_selected(faction, unit_type, unit_name)
        new_state = not current_state
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        unit_info['selected'] = new_state

        logging.debug(f'{unit_name} selection state changed to {new_state}')
        self.update_image_selection(label, new_state, self.is_unit_locked(faction, unit_type, unit_name),
                                    self.get_unit_position(faction, unit_type, unit_name))

        # Update HUD widgets
        for unit_counter, _ in self.hud_windows:
            if isinstance(unit_counter, tuple):
                for uc in unit_counter:
                    uc.update_selected_widgets(faction, unit_type, unit_name, new_state)
            else:
                unit_counter.update_selected_widgets(faction, unit_type, unit_name, new_state)

    def toggle_unit_lock(self, faction, unit_type, unit_name, label):
        """Toggle the lock status of a unit and update HUDs as needed."""
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        new_state = not unit_info.get('locked', False)
        unit_info['locked'] = new_state

        logging.debug(f'{unit_name} lock state changed to {new_state}')
        self.update_image_selection(label, self.is_unit_selected(faction, unit_type, unit_name), new_state,
                                    self.get_unit_position(faction, unit_type, unit_name))

        # Update HUD widgets
        for unit_counter, _ in self.hud_windows:
            if isinstance(unit_counter, tuple):
                for uc in unit_counter:
                    uc.update_locked_widgets(faction, unit_type, unit_name, new_state)
            else:
                unit_counter.update_locked_widgets(faction, unit_type, unit_name, new_state)

    # Visual Update of Unit Image Selection
    # ------------------------------------------------------------------------

    def update_image_selection(self, label, is_selected, is_locked, position):
        """Updates the unit image based on selection, lock, and position state."""
        image_path = label.property("image_path")
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return

        image = pixmap.toImage()

        # Adjust brightness for selection
        self.adjust_image_brightness(image, is_selected)

        # Overlay lock icon if locked
        if is_locked:
            self.overlay_lock_icon(image)

        # Display position if set
        if position > -1:
            self.overlay_position(image, position, is_selected)

        label.setPixmap(QPixmap.fromImage(image))

    def adjust_image_brightness(self, image, is_selected):
        """Adjust image brightness based on selection status."""
        brightness_modifier = 150 if is_selected else -150
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y).lighter(150) if is_selected else color.darker(150)
                image.setPixelColor(x, y, color)

    def overlay_lock_icon(self, image):
        """Overlay a lock icon on the image."""
        painter = QPainter(image)
        lock_icon = QPixmap('lock_icon.png').scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, lock_icon)
        painter.end()

    def overlay_position(self, image, position, is_selected):
        """Overlay the unit's position on the image."""
        painter = QPainter(image)
        painter.setFont(QFont('Arial', 14))
        painter.setPen(Qt.black if is_selected else Qt.white)
        painter.drawText(1, image.height() - 1, str(position))
        painter.end()
