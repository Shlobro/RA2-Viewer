# Main.py

# Standard library imports
import ctypes
import logging
import os
import threading
import time
import traceback
from ctypes import wintypes

# Third-party imports
import psutil
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Signal, QThread, Qt

# Local imports
from Player import ProcessExitedException, initialize_players_after_loading, detect_if_all_players_are_loaded
from logging_config import setup_logging
from UnitData import unit_data
from Settings import settings
from HUDs import HUDs
from ControlPanel import control_panel
from AppState import app_state


# Helper Functions
# -------------------------------------------------------------

def find_pid_by_name(name):
    """Searches for a process by name and returns its PID if found."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None


def find_game_process(stop_event):
    """Waits for the game process to start, returning its PID. Stops if the stop_event is set."""
    logging.info("Waiting for the game to start...")
    while not stop_event.is_set():
        pid = find_pid_by_name("gamemd-spawn.exe")
        if pid is not None:
            logging.info("Game detected")
            return pid
        time.sleep(1)
    return None  # Stop event triggered


def run_create_players_in_background(stop_event):
    """Initializes player creation by detecting and attaching to the game process."""
    app_state.players.clear()

    pid = find_game_process(stop_event)
    if stop_event.is_set() or pid is None:
        logging.error("Invalid PID or stop event set. Exiting.")
        return None

    try:
        process_handle = ctypes.windll.kernel32.OpenProcess(
            wintypes.DWORD(0x1F0FFF), False, pid
        )
        if not process_handle:
            logging.error("Failed to obtain process handle.")
            return None
    except Exception as e:
        logging.error(
            f"Error opening process with PID {pid}: {e}")  # <-- this line changed to handle OpenProcess errors
        return None

    game_process = psutil.Process(pid)

    try:
        # Wait until all players are loaded in the game
        while not detect_if_all_players_are_loaded(process_handle):
            if stop_event.is_set() or not game_process.is_running():
                logging.info("Game process exited before players were loaded.")
                ctypes.windll.kernel32.CloseHandle(process_handle)
                return None
            QThread.msleep(1000)

        try:
            valid_player_count = initialize_players_after_loading(app_state, process_handle)
            if valid_player_count > 0:
                return game_process  # Return the initialized game process object
            else:
                logging.warning("No valid players found.")
                return None
        except Exception as e:
            logging.error(
                f"Failed to initialize players with process handle {process_handle}. Exception: {e}")  # <-- this line changed to add error details
            traceback.print_exc()
            return None

    except Exception as e:
        logging.error(f"Exception in run_create_players_in_background: {e}")
        traceback.print_exc()
        return None


# Handlers for Game Events
# -------------------------------------------------------------

def game_started_handler(app_state, hud_positions, unit_settings):
    """Handles logic when the game starts, initializing and displaying HUDs."""
    logging.info("Game started handler called")
    with app_state.data_lock:
        if not app_state.players:
            logging.info("No valid players found. HUD will not be displayed.")
            return

        HUDs.create_hud_windows(app_state, hud_positions, unit_settings)
        for unit_window, resource_window in HUDs.HUDs_list:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.show()
                else:
                    unit_window.show()


def game_stopped_handler(app_state, hud_positions):
    """Handles logic when the game stops, closing HUDs and clearing player data."""
    logging.info("Game stopped handler called")
    hud_positions.save_hud_positions(app_state)
    for unit_window, resource_window in HUDs.HUDs_list:
        # Close unit windows
        if unit_window:
            if isinstance(unit_window, tuple):
                for uw in unit_window:
                    uw.close()  # closing HUD windows
            else:
                unit_window.close()

        # Close individual resource windows if they exist
        if resource_window.windows:
            for window in resource_window.windows:
                window.close()

    HUDs.HUDs_list.clear()
    app_state.players.clear()

    HUDs.HUDs_list.clear()
    app_state.players.clear()


def on_closing():
    """Closes the control panel and application on program exit."""
    control_panel.on_closing()
    app.quit()


# Background Thread for Data Updates
# -------------------------------------------------------------

class DataUpdateThread(QThread):
    """Thread to monitor game process and update player data."""
    update_signal = Signal()
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.stop_event = threading.Event()

    def run(self):
        try:
            self.setPriority(QThread.LowPriority)  # Attempting to set priority
        except Exception as e:
            logging.warning(
                f"Failed to set thread priority: {e}. Setting normal priority as fallback.")  # <-- this line changed to log fallback
            self.setPriority(QThread.NormalPriority)  # <-- this line changed to log if priority setting fails

        try:
            while not self.stop_event.is_set():
                logging.info("Waiting for the game to start and players to load...")
                game_process = run_create_players_in_background(self.stop_event)
                if game_process is None:
                    if self.stop_event.is_set():
                        logging.info("Stop event set. Exiting thread.")
                        break
                    QThread.msleep(1000)
                    continue

                self.game_started.emit()

                while not self.stop_event.is_set():
                    try:
                        # Check if game process is still running
                        if not game_process.is_running():
                            logging.info("Game process has ended. Exiting monitoring loop.")
                            break
                    except psutil.NoSuchProcess:
                        logging.warning(
                            "Game process no longer exists. Exiting monitoring loop.")
                        break
                    except Exception as e:
                        logging.error(f"Unexpected error while checking game process status: {e}")
                        break

                    try:
                        # Update player data dynamically
                        for player in self.app_state.players:
                            player.update_dynamic_data()
                        self.update_signal.emit()
                    except ProcessExitedException:
                        logging.error(
                            "Process exited unexpectedly. Exiting data update loop.")
                        break
                    except Exception as e:
                        logging.error(
                            f"Unexpected exception during player data update: {e}")
                        traceback.print_exc()
                        break
                    QThread.msleep(1000)

                self.game_stopped.emit()
                logging.info("Emitted game_stopped signal.")

                with self.app_state.data_lock:
                    if self.app_state.process_handle:
                        ctypes.windll.kernel32.CloseHandle(self.app_state.process_handle)
                        self.app_state.process_handle = None
                QThread.msleep(1000)

        except Exception as e:
            logging.error(f"Error in DataUpdateThread: {e}")
            traceback.print_exc()
            self.game_stopped.emit()

        finally:
            with self.app_state.data_lock:
                if self.app_state.process_handle:
                    ctypes.windll.kernel32.CloseHandle(self.app_state.process_handle)
                    self.app_state.process_handle = None
            logging.info("Data update thread has exited.")


# File Path Validation
# -------------------------------------------------------------

def wait_for_current_file_path():
    """Waits until the user selects a valid game file path for spawn.ini."""
    game_path = settings.positions.get('game_path', '')
    spawn_ini_path = os.path.join(game_path, 'spawn.ini')

    new = game_path
    logging.debug(f"Checking spawn.ini path: {spawn_ini_path}")
    while not os.path.exists(spawn_ini_path):
        logging.debug(f"current files path: {game_path}")
        old = new
        QMessageBox.warning(None, "Game Path Error", "Please choose a valid game file path.")
        while old == new:
            logging.debug(f"current files path: {game_path}")
            app.processEvents()
            game_path = settings.positions.get('game_path', '')
            new = game_path
            time.sleep(1)

        spawn_ini_path = os.path.join(game_path, 'spawn.ini')

    logging.info(f"Game path: {game_path}")
    app_state.game_path = game_path


# Main Application Logic
# -------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication([])
    setup_logging()

    # Initialize control panel and start the main loop
    app_state.control_panel = control_panel
    control_panel.show()

    wait_for_current_file_path()

    # Initialize data update thread and connect signals
    data_update_thread = DataUpdateThread(app_state)
    app_state.data_update_thread = data_update_thread

    data_update_thread.update_signal.connect(lambda: HUDs.update_huds(app_state), Qt.QueuedConnection)
    data_update_thread.game_started.connect(lambda: game_started_handler(app_state, settings, unit_data), Qt.QueuedConnection)
    data_update_thread.game_stopped.connect(lambda: game_stopped_handler(app_state, settings), Qt.QueuedConnection)

    data_update_thread.start()
    app.exec()

    # Cleanup on exit
    data_update_thread.stop_event.set()
    data_update_thread.wait()
    unit_data.save_selected_units()
    settings.save_hud_positions(app_state)
