# ControlPanel.py

import logging
import os

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QGroupBox, QFormLayout, QLabel, QSpinBox,
    QCheckBox, QComboBox, QPushButton, QHBoxLayout, QLineEdit, QWidget, QFileDialog, QMessageBox
)

from AppState import app_state
from HUDs import HUDs
from Settings import settings
from UnitSelectionWindow import UnitSelectionWindow


class ControlPanel(QMainWindow):
    """Control Panel GUI for managing HUD settings and game path configurations."""

    def __init__(self):
        super().__init__()
        self.unit_data = settings
        self.app_state = app_state
        self.hud_positions = app_state.settings

        # Main window setup
        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 400, 600)
        main_layout = QVBoxLayout()

        # Unit Window Settings
        main_layout.addWidget(self._create_unit_window_settings_group())

        # Name Widget Settings
        main_layout.addWidget(self._create_name_widget_settings_group())

        # Flag Widget Settings
        main_layout.addWidget(self._create_flag_widget_settings_group())

        # Money Widget Settings
        main_layout.addWidget(self._create_money_widget_settings_group())

        # Power Widget Settings
        main_layout.addWidget(self._create_power_widget_settings_group())

        # Game Path Settings
        main_layout.addWidget(self._create_game_path_settings_group())

        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.on_closing)
        main_layout.addWidget(quit_button)

        # Set main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Store the UnitSelectionWindow instance for reuse
        self.unit_selection_window = None

        # Initialize state based on "Separate Unit Counters" setting
        self._initialize_counter_state()


    # Group Creation Methods
    # ------------------------------------------------------------------------

    def _create_unit_window_settings_group(self):
        """Creates UI components for configuring unit window settings."""
        unit_group = QGroupBox("Unit Window Settings")
        unit_layout = QFormLayout()

        # Unit window size
        self.counter_size_spinbox = self._create_spinbox("unit_counter_size", 5, 250, self.update_unit_window_size)
        unit_layout.addRow("Unit Window Size:", self.counter_size_spinbox)

        # Image Size, Number Size, and Distance for separate mode
        self.image_size_spinbox = self._create_spinbox("image_size", 5, 250, self.update_image_size)
        unit_layout.addRow("Image Size:", self.image_size_spinbox)
        self.number_size_spinbox = self._create_spinbox("number_size", 5, 250, self.update_number_size)
        unit_layout.addRow("Number Size:", self.number_size_spinbox)
        self.distance_spinbox = self._create_spinbox("distance_between_numbers", 0, 150, self.update_distance_between_numbers)
        unit_layout.addRow("Distance Between Numbers:", self.distance_spinbox)

        # Checkboxes
        unit_layout.addRow(self._create_checkbox("Show Unit Frames", "show_unit_frames", self.toggle_unit_frames))
        unit_layout.addRow(self._create_checkbox("Separate Unit Counters", "separate_unit_counters", self.toggle_separate_unit_counters))

        # Layout ComboBox
        layout_label = QLabel("Select Unit Layout:")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        self.layout_combo.setCurrentText(app_state.settings.get('unit_layout', 'Vertical'))
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        unit_layout.addRow(layout_label, self.layout_combo)

        # Unit Selection Button
        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        unit_layout.addRow(selection_button)

        unit_group.setLayout(unit_layout)
        return unit_group

    def _create_name_widget_settings_group(self):
        """Creates UI components for configuring name widget settings."""
        name_group = QGroupBox("Name Widget Settings")
        name_layout = QFormLayout()

        name_layout.addRow(self._create_checkbox("Show Name", "show_name", self.toggle_name))
        self.name_size_spinbox = self._create_spinbox("name_widget_size", 5, 500, self.update_name_widget_size)
        name_layout.addRow("Name Widget Size:", self.name_size_spinbox)

        name_group.setLayout(name_layout)
        return name_group

    def _create_flag_widget_settings_group(self):
        """Creates UI components for configuring flag widget settings."""
        flag_group = QGroupBox("Flag Widget Settings")
        flag_layout = QFormLayout()

        flag_layout.addRow(self._create_checkbox("Show Flag", "show_flag", self.toggle_flag))
        self.flag_size_spinbox = self._create_spinbox("flag_widget_size", 5, 500, self.update_flag_widget_size)
        flag_layout.addRow("Flag Widget Size:", self.flag_size_spinbox)

        flag_group.setLayout(flag_layout)
        return flag_group

    def _create_money_widget_settings_group(self):
        """Creates UI components for configuring money widget settings."""
        money_group = QGroupBox("Money Widget Settings")
        money_layout = QFormLayout()

        money_layout.addRow(self._create_checkbox("Show Money", "show_money", self.toggle_money))
        self.money_size_spinbox = self._create_spinbox("money_widget_size", 5, 500, self.update_money_widget_size)
        money_layout.addRow("Money Widget Size:", self.money_size_spinbox)

        money_color_label = QLabel("Money Text Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Use player color", "White"])
        self.color_combo.setCurrentText(app_state.settings.get('money_color', 'Use player color'))
        self.color_combo.currentTextChanged.connect(self.update_money_color)
        money_layout.addRow(money_color_label, self.color_combo)

        money_group.setLayout(money_layout)
        return money_group

    def _create_power_widget_settings_group(self):
        """Creates UI components for configuring power widget settings."""
        power_group = QGroupBox("Power Widget Settings")
        power_layout = QFormLayout()

        power_layout.addRow(self._create_checkbox("Show Power", "show_power", self.toggle_power))
        self.power_size_spinbox = self._create_spinbox("power_widget_size", 5, 500, self.update_power_widget_size)
        power_layout.addRow("Power Widget Size:", self.power_size_spinbox)

        power_group.setLayout(power_layout)
        return power_group

    def _create_game_path_settings_group(self):
        """Creates UI components for selecting and displaying the game path."""
        path_group = QGroupBox("Game Path Settings")
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setText(app_state.settings.get('game_path', ''))
        self.path_edit.setPlaceholderText("Enter or select the game path")
        path_layout.addWidget(self.path_edit)

        self.path_button = QPushButton("Browse")
        self.path_button.clicked.connect(self.select_game_path)
        path_layout.addWidget(self.path_button)

        path_group.setLayout(path_layout)
        return path_group


    # Utility Methods for UI Component Creation
    # ------------------------------------------------------------------------

    @staticmethod
    def _create_spinbox(setting_key, min_value, max_value, change_handler):
        """Creates a QSpinBox initialized from settings with a handler for value change."""
        spinbox = QSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(app_state.settings.get(setting_key, min_value))
        spinbox.valueChanged.connect(change_handler)
        return spinbox

    @staticmethod
    def _create_checkbox(label, setting_key, change_handler):
        """Creates a QCheckBox initialized from settings with a handler for state change."""
        checkbox = QCheckBox(label)
        checkbox.setChecked(app_state.settings.get(setting_key, False))
        checkbox.stateChanged.connect(change_handler)
        return checkbox


    # Event Handling and Update Methods
    # ------------------------------------------------------------------------

    def toggle_unit_frames(self, state):
        """Toggles the display of unit frames based on the checkbox state."""
        self._update_setting("show_unit_frames", bool(state))

    def toggle_separate_unit_counters(self, state):
        """Enables or disables separate unit counters and adjusts related settings."""
        self._update_setting("separate_unit_counters", bool(state))
        try:
            self._initialize_counter_state()  # Reinitialize UI state
        except Exception as e:
            logging.error(
                f"Error initializing counter state: {e}")
            QMessageBox.critical(self, "Error",
                                 "Failed to update unit counter settings.")

    def toggle_name(self, state):
        """Toggles the display of the name widget."""
        self._update_setting("show_name", bool(state))
        logging.info(f"Toggled 'show_name' to: {bool(state)}")

    def toggle_flag(self, state):
        """Toggles the display of the flag widget."""
        self._update_setting("show_flag", bool(state))
        logging.info(f"Toggled 'show_flag' to: {bool(state)}")

    def toggle_money(self, state):
        """Toggles the display of the money widget."""
        self._update_setting("show_money", bool(state))
        logging.info(f"Toggled 'show_money' to: {bool(state)}")

    def toggle_power(self, state):
        """Toggles the display of the power widget."""
        self._update_setting("show_power", bool(state))
        logging.info(f"Toggled 'show_power' to: {bool(state)}")

    def update_image_size(self):
        self._update_setting("image_size", self.image_size_spinbox.value())

    def update_number_size(self):
        self._update_setting("number_size", self.number_size_spinbox.value())

    def update_distance_between_numbers(self):
        self._update_setting("distance_between_numbers", self.distance_spinbox.value())

    def update_layout(self, layout_type):
        """Updates layout orientation for unit windows."""
        self._update_setting("unit_layout", layout_type)

    def update_unit_window_size(self):
        self._update_setting("unit_counter_size", self.counter_size_spinbox.value())

    def update_name_widget_size(self):
        self._update_setting("name_widget_size", self.name_size_spinbox.value())

    def update_flag_widget_size(self):
        self._update_setting("flag_widget_size", self.flag_size_spinbox.value())

    def update_money_widget_size(self):
        self._update_setting("money_widget_size", self.money_size_spinbox.value())

    def update_power_widget_size(self):
        self._update_setting("power_widget_size", self.power_size_spinbox.value())

    def update_money_color(self, color):
        """Sets the text color of the money widget."""
        self._update_setting("money_color", color)

    def select_game_path(self):
        """Opens a dialog to select the game path, validates it, and saves it in settings if valid."""
        game_path = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if game_path:
            # Validation: Check if 'spawn.ini' exists in the selected directory
            spawn_ini_path = os.path.join(game_path, 'spawn.ini')
            if not os.path.exists(spawn_ini_path):
                QMessageBox.warning(self, "Invalid Path",
                                    "The selected folder does not contain the required game files.")
                return  # Exit without updating if the path is invalid

            # If valid, update the path in settings and QLineEdit
            self.path_edit.setText(game_path)
            self._update_setting("game_path", game_path)

    def open_unit_selection(self):
        """Opens the unit selection window, bringing it to the front if it is already open."""
        if self.unit_selection_window is None:
            self.unit_selection_window = UnitSelectionWindow(self.unit_data, HUDs.HUDs_list)
        if not self.unit_selection_window.isVisible():
            self.unit_selection_window.show()
        else:
            self.unit_selection_window.raise_()  # bring window to front if already open
            self.unit_selection_window.activateWindow()  # give focus to the window

    @staticmethod
    def on_closing():
        """Handles application closing tasks, ensuring a graceful shutdown with error handling."""
        logging.info("Closing application...")
        try:
            settings.save_hud_positions()  # Save HUD positions to settings
            logging.info("HUD positions saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save HUD positions: {e}")  # <-- this line changed to log saving errors

        if app_state.data_update_thread:
            try:
                app_state.data_update_thread.stop_event.set()  # Signal the thread to stop
                app_state.data_update_thread.wait()  # Wait for thread termination
                logging.info("Data update thread has finished.")
            except Exception as e:
                logging.error(
                    f"Error stopping data update thread: {e}")  # <-- this line changed to log thread stop errors

    def _initialize_counter_state(self):
        """Initializes controls based on the 'Separate Unit Counters' setting."""
        separate_mode = app_state.settings.get('separate_unit_counters', False)
        self.image_size_spinbox.setEnabled(separate_mode)
        self.number_size_spinbox.setEnabled(separate_mode)
        self.distance_spinbox.setEnabled(separate_mode)
        self.counter_size_spinbox.setEnabled(not separate_mode)

    def _update_setting(self, key, value):
        """Updates a setting and logs the change."""
        self.app_state.settings[key] = value
        logging.info(f"Updated {key} to: {value}")


# Global instance of ControlPanel
control_panel = ControlPanel()
