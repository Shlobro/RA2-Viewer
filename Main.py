# Standard library imports
import configparser
import ctypes
import json
import logging
import os
import threading
import time
import traceback
from ctypes import wintypes

# Third-party imports
import psutil
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QCheckBox, QVBoxLayout,
    QMainWindow, QLabel, QSpinBox, QComboBox, QFileDialog, QLineEdit, QHBoxLayout, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import QObject, Signal, QThread, Qt

# Local imports
from DataTracker import ResourceWindow
from Player import (
    GameData, initialize_players_after_loading,
    detect_if_all_players_are_loaded, ProcessExitedException
)
from UnitCounter import UnitWindow
from UnitSelectionWindow import UnitSelectionWindow
from logging_config import setup_logging

from common import (HUD_POSITION_FILE, players, hud_windows, selected_units_dict, data_lock, hud_positions,
                    process_handle, control_panel, data_update_thread, names, name_to_path)


# Load HUD positions from file if it exists, otherwise create defaults
def load_hud_positions():
    global hud_positions
    if os.path.exists(HUD_POSITION_FILE):
        with open(HUD_POSITION_FILE, 'r') as file:
            hud_positions = json.load(file)
    else:
        hud_positions = {}

    # Set default values if not present
    hud_positions.setdefault('unit_counter_size', 75)  # Default size is 75
    hud_positions.setdefault('data_counter_size', 50)  # Default size is 50
    hud_positions.setdefault('show_name', True)
    hud_positions.setdefault('show_money', True)
    hud_positions.setdefault('show_power', True)
    hud_positions.setdefault('unit_layout', 'Vertical')  # Default to Vertical layout
    hud_positions.setdefault('money_color', 'Use player color')  # Default to player color
    hud_positions.setdefault('show_flag', True)
    hud_positions.setdefault('flag_widget_size', 50)
    hud_positions.setdefault('show_unit_frames', True)
    # Set default sizes for individual widgets
    hud_positions.setdefault('name_widget_size', 50)
    hud_positions.setdefault('money_widget_size', 50)
    hud_positions.setdefault('power_widget_size', 50)


# Save HUD positions and settings to file
def save_hud_positions():
    global control_panel, hud_positions, hud_windows

    # Save HUD sizes from control panel spin boxes
    if control_panel:
        if control_panel.counter_size_spinbox:
            hud_positions['unit_counter_size'] = control_panel.counter_size_spinbox.value()

        # Save individual widget sizes
        if control_panel.name_size_spinbox:
            hud_positions['name_widget_size'] = control_panel.name_size_spinbox.value()
        if control_panel.money_size_spinbox:
            hud_positions['money_widget_size'] = control_panel.money_size_spinbox.value()
        if control_panel.power_size_spinbox:
            hud_positions['power_widget_size'] = control_panel.power_size_spinbox.value()

        # Save checkbox values
        hud_positions['show_name'] = control_panel.name_checkbox.isChecked()
        hud_positions['show_money'] = control_panel.money_checkbox.isChecked()
        hud_positions['show_power'] = control_panel.power_checkbox.isChecked()
        hud_positions['unit_layout'] = control_panel.layout_combo.currentText()
        hud_positions['show_unit_frames'] = control_panel.unit_frame_checkbox.isChecked()
        # Save the selected color option
        hud_positions['money_color'] = control_panel.color_combo.currentText()

    # Save the game path from the QLineEdit
    if control_panel.path_edit:
        hud_positions['game_path'] = control_panel.path_edit.text()  # Save the game path

    # Save the positions of all HUD windows
    for unit_window, resource_window in hud_windows:
        player_id = resource_window.player.color_name

        # Ensure the player's section exists in the hud_positions
        if player_id not in hud_positions:
            hud_positions[player_id] = {}

        # Save positions for each individual window (name, money, power)
        name_pos = resource_window.windows[0].pos()  # Name window
        money_pos = resource_window.windows[1].pos()  # Money window
        power_pos = resource_window.windows[2].pos()  # Power window
        unit_counter_pos = unit_window.pos()  # Unit counter window
        flag_pos = resource_window.windows[3].pos()  # Flag window

        hud_positions[player_id]['flag'] = {"x": flag_pos.x(), "y": flag_pos.y()}
        hud_positions[player_id]['name'] = {"x": name_pos.x(), "y": name_pos.y()}
        hud_positions[player_id]['money'] = {"x": money_pos.x(), "y": money_pos.y()}
        hud_positions[player_id]['power'] = {"x": power_pos.x(), "y": power_pos.y()}
        hud_positions[player_id]['unit_counter'] = {"x": unit_counter_pos.x(), "y": unit_counter_pos.y()}

    # Write everything to the HUD position file
    with open(HUD_POSITION_FILE, 'w') as file:
        json.dump(hud_positions, file, indent=4)


# Find the PID of a process by name
def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


# Wait for the game process to start and return its PID
def find_game_process(stop_event):
    logging.info("Waiting for the game to start...")
    while not stop_event.is_set():
        pid = find_pid_by_name("gamemd-spawn.exe")
        if pid is not None:
            logging.info("Game detected")
            return pid
        time.sleep(1)
    return None  # Return None if stop_event is set


# Run player creation in the background
def run_create_players_in_background(stop_event):
    global players, game_data, process_handle

    players.clear()
    game_data = GameData()

    # Find the game process
    pid = find_game_process(stop_event)
    if pid is None or stop_event.is_set():
        return None  # Game process not found or stop event set

    # Obtain the process handle
    process_handle = ctypes.windll.kernel32.OpenProcess(
        wintypes.DWORD(0x1F0FFF), False, pid
    )

    if not process_handle:
        logging.error("Failed to obtain process handle.")
        return None

    game_process = psutil.Process(pid)

    try:
        # Wait until players are loaded
        while not detect_if_all_players_are_loaded(process_handle):
            if stop_event.is_set():
                return None
            if not game_process.is_running():
                logging.info("Game process exited before players were loaded.")
                # Close the process handle
                ctypes.windll.kernel32.CloseHandle(process_handle)
                process_handle = None
                return None
            QThread.msleep(1000)

        # Initialize players after loading
        valid_player_count = initialize_players_after_loading(game_data, process_handle)
        if valid_player_count > 0:
            players = game_data.players
            return game_process  # Return the game_process object
        else:
            logging.warning("No valid players found.")
            return None
    except Exception as e:
        logging.error(f"Exception in run_create_players_in_background: {e}")
        traceback.print_exc()
        return None


# Create HUD windows for each player
def create_hud_windows():
    global hud_windows

    # Step 1: Get the game path and check for spawn.ini
    game_path = hud_positions.get('game_path', '')
    spawn_ini_path = os.path.join(game_path, 'spawn.ini')

    logging.debug("spawn_ini_path")

    if not os.path.exists(spawn_ini_path):
        # Step 2: If spawn.ini does not exist, show a warning message
        QMessageBox.warning(None, "Game Path Error", "Please choose a valid game file path.")
        return

    # Step 3: Parse the spawn.ini file
    config = configparser.ConfigParser()
    config.read(spawn_ini_path)

    # Step 4: Check if 'IsSpectator' is set to 'True'
    is_spectator = config.get('Settings', 'IsSpectator', fallback='False').lower() in ['true', 'yes']

    if not is_spectator:
        # Step 5: Show a warning if the player is not in spectator mode
        QMessageBox.warning(None, "Spectator Mode Required", "You can only use the Unit counter in Spectator mode.")
        return

    # Step 6: Close any existing HUD windows before creating new ones
    for unit_window, resource_window in hud_windows:
        unit_window.close()
        resource_window.close()
    hud_windows = []

    if len(players) == 0:
        logging.info("No valid players found. HUD will not be displayed.")
        return

    # Step 7: Create the HUD windows
    for player in players:
        logging.info(f"Creating HUD for {player.username.value} with color {player.color_name}")
        unit_window = UnitWindow(player, len(players), hud_positions, selected_units_dict)
        unit_window.setWindowTitle(f"Player {player.color_name} unit window")
        resource_window = ResourceWindow(player, len(players), hud_positions, player.color_name)
        resource_window.setWindowTitle(f"Player {player.color_name} resource window")
        hud_windows.append((unit_window, resource_window))


# Update the HUDs with the latest data
def update_huds():
    if len(hud_windows) == 0:
        return  # No HUDs to update
    try:
        for unit_window, resource_window in hud_windows:
            unit_window.update_labels()
            resource_window.update_labels()
    except Exception as e:
        logging.error(f"Exception in update_huds: {e}")
        traceback.print_exc()


# Handler for when the game starts
def game_started_handler():
    logging.info("Game started handler called")
    with data_lock:
        if len(players) == 0:
            logging.info("No valid players found. HUD will not be displayed.")
            return
        # Create HUD windows
        create_hud_windows()
        for unit_window, resource_window in hud_windows:
            unit_window.show()


# Handler for when the game stops
def game_stopped_handler():
    logging.info("Game stopped handler called")
    save_hud_positions()  # Save the positions of HUD windows

    # Close all HUD windows (unit window, resource window)
    for unit_window, resource_window in hud_windows:
        # Close unit counter window
        unit_window.close()

        # Close each individual resource window (name, money, power)
        for window in resource_window.windows:
            window.close()

    hud_windows.clear()  # Clear the HUD windows list
    players.clear()  # Clear the players list


# Handle closing the application
def on_closing():
    global data_update_thread
    logging.info("Closing application...")
    save_hud_positions()
    # Signal the thread to stop
    if data_update_thread:
        data_update_thread.stop_event.set()
        # Wait for the thread to finish
        data_update_thread.wait()
        logging.info("Data update thread has finished.")
    app.quit()


def save_selected_units():
    """Save the selected units to the JSON file."""
    json_file = 'unit_selection.json'

    with open(json_file, 'w') as file:
        json.dump(selected_units_dict, file, indent=4)

    logging.info("Saved selected units.")


# Control Panel for HUD settings
class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()

        global selected_units_dict
        selected_units_dict = self.load_selected_units()

        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 400, 600)  # Adjusted window size

        main_layout = QVBoxLayout()

        # Unit Window Settings Group
        unit_group = QGroupBox("Unit Window Settings")
        unit_layout = QFormLayout()

        unit_size_label = QLabel("Unit Window Size:")
        counter_size = hud_positions.get('unit_counter_size', 75)
        self.counter_size_spinbox = QSpinBox()
        self.counter_size_spinbox.setRange(25, 250)
        self.counter_size_spinbox.setValue(counter_size)
        self.counter_size_spinbox.valueChanged.connect(self.update_unit_window_size)
        unit_layout.addRow(unit_size_label, self.counter_size_spinbox)

        self.unit_frame_checkbox = QCheckBox("Show Unit Frames")
        self.unit_frame_checkbox.setChecked(hud_positions.get('show_unit_frames', True))
        self.unit_frame_checkbox.stateChanged.connect(self.toggle_unit_frames)
        unit_layout.addRow(self.unit_frame_checkbox)

        # Unit Selection Section
        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        unit_layout.addRow(selection_button)

        unit_group.setLayout(unit_layout)
        main_layout.addWidget(unit_group)

        # Layout Settings Group
        layout_group = QGroupBox("Layout Settings")
        layout_group_layout = QVBoxLayout()

        # Layout Type Selection
        layout_type_layout = QHBoxLayout()
        layout_label = QLabel("Select Unit Layout:")
        layout_type_layout.addWidget(layout_label)

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        layout_type = hud_positions.get('unit_layout', 'Vertical')
        self.layout_combo.setCurrentText(layout_type)
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        layout_type_layout.addWidget(self.layout_combo)

        layout_group_layout.addLayout(layout_type_layout)
        layout_group.setLayout(layout_group_layout)
        main_layout.addWidget(layout_group)

        # Name Widget Settings Group
        name_group = QGroupBox("Name Widget Settings")
        name_layout = QFormLayout()

        self.name_checkbox = QCheckBox("Show Name")
        self.name_checkbox.setChecked(hud_positions.get('show_name'))
        self.name_checkbox.stateChanged.connect(self.toggle_name)
        name_layout.addRow(self.name_checkbox)

        name_size_label = QLabel("Name Widget Size:")
        name_size = hud_positions.get('name_widget_size', 50)
        self.name_size_spinbox = QSpinBox()
        self.name_size_spinbox.setRange(10, 100)
        self.name_size_spinbox.setValue(name_size)
        self.name_size_spinbox.valueChanged.connect(self.update_name_widget_size)
        name_layout.addRow(name_size_label, self.name_size_spinbox)

        name_group.setLayout(name_layout)
        main_layout.addWidget(name_group)

        # Flag Widget Settings Group
        flag_group = QGroupBox("Flag Widget Settings")
        flag_layout = QFormLayout()

        self.flag_checkbox = QCheckBox("Show Flag")
        self.flag_checkbox.setChecked(hud_positions.get('show_flag', True))
        self.flag_checkbox.stateChanged.connect(self.toggle_flag)
        flag_layout.addRow(self.flag_checkbox)

        flag_size_label = QLabel("Flag Widget Size:")
        flag_size = hud_positions.get('flag_widget_size', 50)
        self.flag_size_spinbox = QSpinBox()
        self.flag_size_spinbox.setRange(10, 100)
        self.flag_size_spinbox.setValue(flag_size)
        self.flag_size_spinbox.valueChanged.connect(self.update_flag_widget_size)
        flag_layout.addRow(flag_size_label, self.flag_size_spinbox)

        flag_group.setLayout(flag_layout)
        main_layout.addWidget(flag_group)

        # Money Widget Settings Group
        money_group = QGroupBox("Money Widget Settings")
        money_layout = QFormLayout()

        self.money_checkbox = QCheckBox("Show Money")
        self.money_checkbox.setChecked(hud_positions.get('show_money'))
        self.money_checkbox.stateChanged.connect(self.toggle_money)
        money_layout.addRow(self.money_checkbox)

        money_size_label = QLabel("Money Widget Size:")
        money_size = hud_positions.get('money_widget_size', 50)
        self.money_size_spinbox = QSpinBox()
        self.money_size_spinbox.setRange(10, 100)
        self.money_size_spinbox.setValue(money_size)
        self.money_size_spinbox.valueChanged.connect(self.update_money_widget_size)
        money_layout.addRow(money_size_label, self.money_size_spinbox)

        money_color_label = QLabel("Money Text Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Use player color", "White"])
        money_color = hud_positions.get('money_color', 'Use player color')
        self.color_combo.setCurrentText(money_color)
        self.color_combo.currentTextChanged.connect(self.update_money_color)
        money_layout.addRow(money_color_label, self.color_combo)

        money_group.setLayout(money_layout)
        main_layout.addWidget(money_group)

        # Power Widget Settings Group
        power_group = QGroupBox("Power Widget Settings")
        power_layout = QFormLayout()

        self.power_checkbox = QCheckBox("Show Power")
        self.power_checkbox.setChecked(hud_positions.get('show_power'))
        self.power_checkbox.stateChanged.connect(self.toggle_power)
        power_layout.addRow(self.power_checkbox)

        power_size_label = QLabel("Power Widget Size:")
        power_size = hud_positions.get('power_widget_size', 50)
        self.power_size_spinbox = QSpinBox()
        self.power_size_spinbox.setRange(10, 100)
        self.power_size_spinbox.setValue(power_size)
        self.power_size_spinbox.valueChanged.connect(self.update_power_widget_size)
        power_layout.addRow(power_size_label, self.power_size_spinbox)

        power_group.setLayout(power_layout)
        main_layout.addWidget(power_group)

        # Game Path Settings Group
        path_group = QGroupBox("Game Path Settings")
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        game_path = hud_positions.get('game_path', '')
        self.path_edit.setText(game_path)
        self.path_edit.setPlaceholderText("Enter or select the game path")
        path_layout.addWidget(self.path_edit)

        self.path_button = QPushButton("Browse")
        self.path_button.clicked.connect(self.select_game_path)
        path_layout.addWidget(self.path_button)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(on_closing)
        main_layout.addWidget(quit_button)

        # Set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Store the reference to the UnitSelectionWindow here
        self.unit_selection_window = None

    def toggle_unit_frames(self, state):
        hud_positions['show_unit_frames'] = (state == 0)
        logging.info(f"Toggled show_unit_frames to: {hud_positions['show_unit_frames']}")

        # Update all existing CounterWidgets
        if hud_windows:
            for unit_window, _ in hud_windows:
                unit_window.update_show_unit_frames(hud_positions['show_unit_frames'])

    # Add methods for the flag widget
    def update_flag_widget_size(self):
        new_size = self.flag_size_spinbox.value()
        hud_positions['flag_widget_size'] = new_size
        logging.info(f"Updated flag widget size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.flag_widget.update_data_size(new_size)

    def toggle_flag(self, state):
        self.toggle_hud_element('show_flag', 'flag_widget', state)

    # Update toggle_hud_element to include the flag_widget
    def toggle_hud_element(self, element, widget_name, state):
        hud_positions[element] = (state == 2)
        logging.info(f"Toggled {element} state to: {hud_positions[element]}")

        # If HUD windows exist, toggle visibility of the specified widget
        if hud_windows:
            index_mapping = {
                'name_widget': 0,
                'money_widget': 1,
                'power_widget': 2,
                'flag_widget': 3  # Add the flag widget index
            }
            index = index_mapping.get(widget_name)
            if index is not None:
                for _, resource_window in hud_windows:
                    window = resource_window.windows[index]
                    if state == 2:
                        window.show()
                    else:
                        window.hide()

    def select_game_path(self):
        # Open the folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if folder_path:
            # Set the folder path in the text box
            self.path_edit.setText(folder_path)

    def update_money_color(self, color):
        """Update the selected money color."""
        color = color.strip()
        hud_positions['money_color'] = color
        logging.info(f"HUD money color updated to: '{color}'")

        # If HUD windows exist, update their money widget colors
        if hud_windows:
            for _, resource_window in hud_windows:
                logging.debug(f"Updating money widget color for player {resource_window.player.username.value}")
                resource_window.update_money_widget_color()

    def update_layout(self, layout_type):
        """Update the layout of the UnitWindow between vertical and horizontal."""
        hud_positions['unit_layout'] = layout_type
        logging.info(f"Updated layout to: {layout_type}")

        # If HUD windows exist, update their layouts as well
        if hud_windows:
            for unit_window, _ in hud_windows:
                unit_window.update_layout(layout_type)
        else:
            logging.info("HUD windows do not exist yet, storing the layout for later.")

    def update_unit_window_size(self):
        new_size = self.counter_size_spinbox.value()
        hud_positions['unit_counter_size'] = new_size
        logging.info(f"Updated unit window size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for unit_window, _ in hud_windows:
                unit_window.update_all_counters_size(new_size)

    def update_name_widget_size(self):
        new_size = self.name_size_spinbox.value()
        hud_positions['name_widget_size'] = new_size
        logging.info(f"Updated name widget size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.name_widget.update_data_size(new_size)

    def update_money_widget_size(self):
        new_size = self.money_size_spinbox.value()
        hud_positions['money_widget_size'] = new_size
        logging.info(f"Updated money widget size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.money_widget.update_data_size(new_size)

    def update_power_widget_size(self):
        new_size = self.power_size_spinbox.value()
        hud_positions['power_widget_size'] = new_size
        logging.info(f"Updated power widget size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.power_widget.update_data_size(new_size)

    # Method to open the Unit Selection window
    def open_unit_selection(self):
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow(selected_units_dict, hud_windows)
            logging.info("Opening Unit Selection window")
            self.unit_selection_window.show()

    def load_selected_units(self):
        """Load the selected units from the JSON file."""
        json_file = 'unit_selection.json'
        if os.path.exists(json_file):
            with open(json_file, 'r') as file:
                data = json.load(file)
                return data  # Return the entire data
        return {}

    # Method to toggle the visibility of HUD elements

    # Then you can call this method for different elements
    def toggle_name(self, state):
        self.toggle_hud_element('show_name', 'name_widget', state)

    def toggle_money(self, state):
        self.toggle_hud_element('show_money', 'money_widget', state)

    def toggle_power(self, state):
        self.toggle_hud_element('show_power', 'power_widget', state)

    def toggle_separate(self, state):
        self.toggle_hud_element('separate_info', 'separate_info', state)


# Thread to continuously update player data
class DataUpdateThread(QThread):
    update_signal = Signal()
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def run(self):
        self.setPriority(QThread.LowPriority)
        global process_handle
        try:
            while not self.stop_event.is_set():
                logging.info("Waiting for the game to start and players to load...")
                game_process = run_create_players_in_background(self.stop_event)
                if game_process is None:
                    if self.stop_event.is_set():
                        logging.info("Stop event set. Exiting thread.")
                        break
                    QThread.msleep(1000)
                    continue  # Retry if the game process is not found

                # Emit game_started signal now that players are initialized
                self.game_started.emit()

                # Now we have 'game_process' defined and can use it
                while not self.stop_event.is_set():
                    try:
                        if not game_process.is_running():
                            logging.info("Game process has ended.")
                            break
                    except psutil.NoSuchProcess:
                        logging.warning("Game process no longer exists.")
                        break

                    try:
                        for player in players:
                            player.update_dynamic_data()
                        self.update_signal.emit()  # Emit signal after data update
                    except ProcessExitedException:
                        logging.error("Process has exited. Exiting data update loop.")
                        break  # Exit the inner loop
                    except Exception as e:
                        logging.error(f"Exception during updating player data: {e}")
                        traceback.print_exc()
                        break  # Exit the inner loop
                    QThread.msleep(1000)

                # Game has ended or exception occurred
                self.game_stopped.emit()
                logging.info("Emitted game_stopped signal.")

                # Close process_handle
                with data_lock:
                    if process_handle:
                        ctypes.windll.kernel32.CloseHandle(process_handle)
                        process_handle = None

                QThread.msleep(1000)

        except Exception as e:
            logging.error(f"Error in DataUpdateThread: {e}")
            traceback.print_exc()
            self.game_stopped.emit()  # Ensure the signal is emitted

        finally:
            with data_lock:
                if process_handle:
                    ctypes.windll.kernel32.CloseHandle(process_handle)
                    process_handle = None
            logging.info("Data update thread has exited.")


# Main application logic
if __name__ == '__main__':
    app = QApplication([])
    setup_logging()
    # Load HUD positions
    load_hud_positions()

    # Initialize the control panel
    control_panel = ControlPanel()
    control_panel.show()

    # Start the data update thread
    data_update_thread = DataUpdateThread()

    # Connect signals from data_update_thread with Qt.QueuedConnection
    data_update_thread.update_signal.connect(update_huds, Qt.QueuedConnection)
    data_update_thread.game_started.connect(game_started_handler, Qt.QueuedConnection)
    data_update_thread.game_stopped.connect(game_stopped_handler, Qt.QueuedConnection)

    data_update_thread.start()

    app.exec()

    # On application exit
    data_update_thread.stop_event.set()
    data_update_thread.wait()
    save_selected_units()
    save_hud_positions()
