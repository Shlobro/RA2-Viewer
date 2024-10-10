# Standard library imports
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
    QMainWindow, QLabel, QSpinBox
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

# Constants
HUD_POSITION_FILE = 'hud_positions.json'

# Global variables
players = []           # List to store player objects
hud_windows = []       # List to store HUDWindow objects
data_lock = threading.Lock()
hud_positions = {}     # Dictionary to store HUD positions and settings
process_handle = None  # Handle for the game process
control_panel = None   # Reference to the ControlPanel instance
data_update_thread = None  # Reference to the DataUpdateThread instance


# Load HUD positions from file if it exists, otherwise create defaults
def load_hud_positions():
    global hud_positions
    if os.path.exists(HUD_POSITION_FILE):
        with open(HUD_POSITION_FILE, 'r') as file:
            hud_positions = json.load(file)
    else:
        hud_positions = {}

    # Set default values if not present
    hud_positions.setdefault('unit_counter_size', 100)  # Default size is 100
    hud_positions.setdefault('data_counter_size', 16)   # Default size is 16
    hud_positions.setdefault('show_name', True)
    hud_positions.setdefault('show_money', True)
    hud_positions.setdefault('show_power', True)


# Save HUD positions and settings to file
def save_hud_positions():
    global control_panel, hud_positions
    if control_panel:
        # Update HUD sizes from control panel spin boxes
        if control_panel.counter_size_spinbox:
            hud_positions['unit_counter_size'] = control_panel.counter_size_spinbox.value()
        if control_panel.data_size_spinbox:
            hud_positions['data_counter_size'] = control_panel.data_size_spinbox.value()

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
            time.sleep(1)

        # Initialize players after loading
        valid_player_count = initialize_players_after_loading(game_data, process_handle)
        if valid_player_count > 0:
            players = game_data.players
            return game_process  # Return the game_process object
        else:
            logging.info("No valid players found.")
            return None
    except Exception as e:
        logging.error(f"Exception in run_create_players_in_background: {e}")
        traceback.print_exc()
        return None


# Create HUD windows for each player
def create_hud_windows():
    global hud_windows
    # Close any existing HUD windows
    for unit_window, resource_window in hud_windows:
        unit_window.close()
        resource_window.close()
    hud_windows = []

    if len(players) == 0:
        logging.info("No valid players found. HUD will not be displayed.")
        return

    for player in players:
        logging.info(f"Creating HUD for {player.username.value} with color {player.color}")
        unit_window = UnitWindow(player, len(players), hud_positions)
        resource_window = ResourceWindow(player, len(players), hud_positions)
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
            resource_window.show()


# Handler for when the game stops
def game_stopped_handler():
    logging.info("Game stopped handler called")
    for unit_window, resource_window in hud_windows:
        unit_window.close()
        resource_window.close()
    hud_windows.clear()
    players.clear()


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

# Control Panel for HUD settings
class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 300, 250)

        layout = QVBoxLayout()

        # Add a button to open the Unit Selection window
        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        layout.addWidget(selection_button)

        self.name_checkbox = QCheckBox("Show Name")
        self.name_checkbox.setChecked(hud_positions.get('show_name', True))
        self.name_checkbox.stateChanged.connect(self.toggle_name)
        layout.addWidget(self.name_checkbox)

        self.money_checkbox = QCheckBox("Show Money")
        self.money_checkbox.setChecked(hud_positions.get('show_money', True))
        self.money_checkbox.stateChanged.connect(self.toggle_money)
        layout.addWidget(self.money_checkbox)

        self.power_checkbox = QCheckBox("Show Power")
        self.power_checkbox.setChecked(hud_positions.get('show_power', True))
        self.power_checkbox.stateChanged.connect(self.toggle_power)
        layout.addWidget(self.power_checkbox)

        # Add the QSpinBox for resizing the UnitWindow
        self.size_label = QLabel("Set Unit Window Size: (25 - 250)")
        layout.addWidget(self.size_label)

        counter_size = hud_positions.get('unit_counter_size', 100)
        self.counter_size_spinbox = QSpinBox()
        self.counter_size_spinbox.setRange(25, 250)
        self.counter_size_spinbox.setValue(counter_size)
        self.counter_size_spinbox.valueChanged.connect(self.update_unit_window_size)
        layout.addWidget(self.counter_size_spinbox)

        # Add QSpinBox for resizing the ResourceWindow (DataWindow)
        self.data_size_label = QLabel("Set Data Window Size: (10 - 100)")
        layout.addWidget(self.data_size_label)

        data_size = hud_positions.get('data_counter_size', 16)
        self.data_size_spinbox = QSpinBox()
        self.data_size_spinbox.setRange(10, 100)
        self.data_size_spinbox.setValue(data_size)
        self.data_size_spinbox.valueChanged.connect(self.update_data_window_size)
        layout.addWidget(self.data_size_spinbox)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(on_closing)
        layout.addWidget(quit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Store the reference to the UnitSelectionWindow here
        self.unit_selection_window = None

    def update_unit_window_size(self):
        new_size = self.counter_size_spinbox.value()
        hud_positions['unit_counter_size'] = new_size
        logging.info(f"Updated unit window size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for unit_window, _ in hud_windows:
                unit_window.update_all_counters_size(new_size)

    def update_data_window_size(self):
        new_size = self.data_size_spinbox.value()
        hud_positions['data_counter_size'] = new_size
        logging.info(f"Updated data window size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.update_all_data_size(new_size)

    # Method to open the Unit Selection window
    def open_unit_selection(self):
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow('unit_selection.json')
            logging.info("Opening Unit Selection window")
            self.unit_selection_window.show()

    # Method to toggle the visibility of Name
    def toggle_name(self, state):
        hud_positions['show_name'] = (state == 2)
        logging.info(f"Toggled show name state to: {hud_positions['show_name']}")

        # If HUD windows exist, toggle visibility of the name widget
        if hud_windows:
            for _, resource_window in hud_windows:
                if state == 2:
                    resource_window.name_widget.show()
                else:
                    resource_window.name_widget.hide()

    # Method to toggle the visibility of Money
    def toggle_money(self, state):
        hud_positions['show_money'] = (state == 2)
        logging.info(f"Toggled show money state to: {hud_positions['show_money']}")

        # If HUD windows exist, toggle visibility of the money widget
        if hud_windows:
            for _, resource_window in hud_windows:
                if state == 2:
                    resource_window.money_widget.show()
                else:
                    resource_window.money_widget.hide()

    # Method to toggle the visibility of Power
    def toggle_power(self, state):
        hud_positions['show_power'] = (state == 2)
        logging.info(f"Toggled show power state to: {hud_positions['show_power']}")

        # If HUD windows exist, toggle visibility of the power widget
        if hud_windows:
            for _, resource_window in hud_windows:
                if state == 2:
                    resource_window.power_widget.show()
                else:
                    resource_window.power_widget.hide()


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
    save_hud_positions()
