import ctypes
import json
import os
import threading
import time
from ctypes import wintypes
import traceback
import psutil
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QVBoxLayout, QMainWindow, QLabel, QSpinBox
from PySide6.QtCore import QObject, Signal
from DataTracker import ResourceWindow
from Player import GameData, initialize_players_after_loading, detect_if_all_players_are_loaded
from UnitCounter import UnitWindow
from UnitSelectionWindow import UnitSelectionWindow
from PySide6.QtCore import QThread

# Global variable for player count (default 2 players)
player_count = 0
hud_position_file = 'hud_positions.json'

# List to store player objects
players = []
hud_windows = []  # List to store HUDWindow objects
data_lock = threading.Lock()

# Update the create_hud_windows function to create both Unit and Resource windows
def create_hud_windows():
    global hud_windows
    # Close any existing HUD windows
    for unit_window, resource_window in hud_windows:
        unit_window.close()
        resource_window.close()
    hud_windows = []

    if len(players) == 0:
        print("No valid players found. HUD will not be displayed.")
        return

    for player in players:
        print(f"Now creating HUD for {player.username.value} and his color is {player.color}")
        unit_window = UnitWindow(player, len(players), hud_positions)
        resource_window = ResourceWindow(player, len(players), hud_positions)
        hud_windows.append((unit_window, resource_window))



# Load HUD positions from file if it exists, otherwise create default
def load_hud_positions():
    if not os.path.exists(hud_position_file):
        return {}

    with open(hud_position_file, 'r') as file:
        hud_positions = json.load(file)

    # Set default size globally if not present
    if 'unit_counter_size' not in hud_positions:
        hud_positions['unit_counter_size'] = 100  # Default size is 100

    # Set default size globally if not present
    if 'data_counter_size' not in hud_positions:
        hud_positions['data_counter_size'] = 16  # Default size is 16

    return hud_positions


# Save HUD positions to file
def save_hud_positions():
    # Check if the control panel has the size_spinbox and retrieve the value from there
    if control_panel.counter_size_spinbox:
        unit_counter_size = control_panel.counter_size_spinbox.value()  # Get size from the ControlPanel's size_spinbox
        hud_positions['unit_counter_size'] = unit_counter_size

        # Check if the control panel has the size_spinbox and retrieve the value from there
    if control_panel.counter_size_spinbox:
        data_counter_size = control_panel.data_size_spinbox.value()  # Get size from the ControlPanel's size_spinbox
        hud_positions['data_counter_size'] = data_counter_size

    with open(hud_position_file, 'w') as file:
        json.dump(hud_positions, file, indent=4)



def find_game_process(stop_event):
    print("Waiting for the game to start...")
    while not stop_event.is_set():
        pid = find_pid_by_name("gamemd-spawn.exe")
        if pid is not None:
            print("Game detected")
            return pid
        time.sleep(1)
    return None  # Return None if stop event is set



def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


def update_huds():
    with data_lock:
        if len(hud_windows) == 0:
            return  # No HUDs to update
        try:
            for unit_window, resource_window in hud_windows:
                unit_window.update_labels()
                resource_window.update_labels()
        except Exception as e:
            print(f"Exception in update_huds: {e}")
            traceback.print_exc()



# Function to toggle HUD visibility (show/hide all HUDs)
hud_visible = True


# Handle closing the application
def on_closing():
    print("Closing application...")
    save_hud_positions()
    # Signal the thread to stop
    data_update_thread.stop_event.set()
    # Wait for the thread to finish
    data_update_thread.wait()
    print("Data update thread has finished.")
    app.quit()



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
        self.name_checkbox.setChecked(True)
        self.name_checkbox.stateChanged.connect(self.toggle_name)
        layout.addWidget(self.name_checkbox)

        self.money_checkbox = QCheckBox("Show Money")
        self.money_checkbox.setChecked(True)
        self.money_checkbox.stateChanged.connect(self.toggle_money)
        layout.addWidget(self.money_checkbox)

        self.power_checkbox = QCheckBox("Show Power")
        self.power_checkbox.setChecked(True)
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

        data_size = hud_positions.get('data_counter_size', 16)  # Default to 16 for data windows
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
        # Update the hud_positions dictionary, even if HUD windows are not initialized yet
        hud_positions['unit_counter_size'] = new_size
        print(f"Updated unit window size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for unit_window, _ in hud_windows:
                unit_window.update_all_counters_size(new_size)

    def update_data_window_size(self):
        new_size = self.data_size_spinbox.value()
        # Update the hud_positions dictionary, even if HUD windows are not initialized yet
        hud_positions['data_counter_size'] = new_size
        print(f"Updated data window size in hud_positions: {new_size}")

        # If HUD windows exist, update their sizes as well
        if hud_windows:
            for _, resource_window in hud_windows:
                resource_window.update_all_data_size(new_size)

    # Method to open the Unit Selection window and keep it open
    def open_unit_selection(self):
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow('unit_selection.json')
            self.unit_selection_window.show()


    # Method to toggle the visibility of Money
    def toggle_name(self, state):
        # Update the hud_positions dictionary for future HUDs
        hud_positions['show_name'] = (state == 2)
        print(f"Updated show money state in hud_positions: {hud_positions['show_name']}")

        # If HUD windows exist, toggle visibility of the money widget
        if hud_windows:
            for _, name_window in hud_windows:
                if state == 2:
                    name_window.name_widget.show()
                else:
                    name_window.name_widget.hide()

    # Method to toggle the visibility of Money
    def toggle_money(self, state):
        # Update the hud_positions dictionary for future HUDs
        hud_positions['show_money'] = (state == 2)
        print(f"Updated show money state in hud_positions: {hud_positions['show_money']}")

        # If HUD windows exist, toggle visibility of the money widget
        if hud_windows:
            for _, resource_window in hud_windows:
                if state == 2:
                    resource_window.money_widget.show()
                else:
                    resource_window.money_widget.hide()

    # Method to toggle the visibility of Power
    def toggle_power(self, state):
        # Update the hud_positions dictionary for future HUDs
        hud_positions['show_power'] = (state == 2)
        print(f"Updated show power state in hud_positions: {hud_positions['show_power']}")

        # If HUD windows exist, toggle visibility of the power widget
        if hud_windows:
            for _, resource_window in hud_windows:
                if state == 2:
                    resource_window.power_widget.show()
                else:
                    resource_window.power_widget.hide()


# Store the HUD positions in memory
hud_positions = load_hud_positions()


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
        wintypes.DWORD(0x0010 | 0x0020 | 0x0008 | 0x0010), False, pid)

    if not process_handle:
        print("Error: Failed to obtain process handle.")
        return None

    game_process = psutil.Process(pid)

    try:
        # Wait until players are loaded
        while not detect_if_all_players_are_loaded(process_handle):
            if stop_event.is_set():
                return None
            if not game_process.is_running():
                print("Game process exited before players were loaded.")
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
            print("No valid players found.")
            return None
    except Exception as e:
        print(f"Exception in run_create_players_in_background: {e}")
        traceback.print_exc()
        return None




def game_started_handler():
    print("Game started handler called")
    with data_lock:
        if len(players) == 0:
            print("No valid players found. HUD will not be displayed.")
            return
        # Create HUD windows
        create_hud_windows()
        for unit_window, resource_window in hud_windows:
            unit_window.show()
            resource_window.show()

def game_stopped_handler():
    print("Game stopped handler called")
    with data_lock:
        for unit_window, resource_window in hud_windows:
            unit_window.close()  # Close the windows
            resource_window.close()
        hud_windows.clear()
        players.clear()




class DataUpdateThread(QThread):
    update_signal = Signal()
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def run(self):
        global process_handle  # Ensure process_handle is accessible
        try:
            while not self.stop_event.is_set():
                print("Waiting for the game to start and players to load...")
                game_process = run_create_players_in_background(self.stop_event)
                if game_process is None:
                    if self.stop_event.is_set():
                        print("Stop event set. Exiting thread.")
                        break
                    time.sleep(1)
                    continue  # Retry if the game process is not found

                # Emit game_started signal now that players are initialized
                self.game_started.emit()

                while game_process.is_running() and not self.stop_event.is_set():
                    with data_lock:
                        try:
                            for player in players:
                                player.update_dynamic_data()
                            self.update_signal.emit()  # Emit signal after data update
                        except Exception as e:
                            print(f"Exception during updating player data: {e}")
                            traceback.print_exc()
                            break  # Exit the loop
                    time.sleep(1)

                if self.stop_event.is_set():
                    print("Stop event set during game loop. Exiting thread.")
                    break

                # Game has ended
                self.game_stopped.emit()  # Emit game_stopped signal
                print("Game process ended.")

                # Close process_handle
                with data_lock:
                    if process_handle:
                        ctypes.windll.kernel32.CloseHandle(process_handle)
                        process_handle = None
                time.sleep(1)
        except Exception as e:
            print(f"Error in DataUpdateThread: {e}")
            traceback.print_exc()
        finally:
            with data_lock:
                if process_handle:
                    ctypes.windll.kernel32.CloseHandle(process_handle)
                    process_handle = None
            print("Data update thread has exited.")


# Main application loop
if __name__ == '__main__':
    app = QApplication([])

    # hud_updater = HUDUpdater()  # Remove this line

    control_panel = ControlPanel()
    control_panel.show()

    # Start the background thread
    data_update_thread = DataUpdateThread()

    # Connect signals from data_update_thread
    data_update_thread.update_signal.connect(update_huds)
    data_update_thread.game_started.connect(game_started_handler)
    data_update_thread.game_stopped.connect(game_stopped_handler)

    data_update_thread.start()

    app.exec()

    # On application exit
    data_update_thread.stop_event.set()
    data_update_thread.quit()
    data_update_thread.wait()
    save_hud_positions()

