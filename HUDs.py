# HUDs.py

import configparser
import logging
import os
import traceback
from PySide6.QtWidgets import QMessageBox

from AppState import app_state
from DataTracker import ResourceWindow
from Settings import settings
from SelectedUnits import selected_units
from UnitWindow import UnitWindowImagesOnly, UnitWindowNumbersOnly, UnitWindowWithImages


class HUD:
    """Manages HUD display and updates for each player, including unit and resource windows."""

    def __init__(self):
        # List to hold HUD window references (unit windows and resource windows)
        self.HUDs_list = []

    # HUD Creation and Management
    # ------------------------------------------------------------------------

    def create_hud_windows(self):
        """Creates HUD windows for each player if in Spectator mode, displaying unit and resource information."""

        if not app_state.admin:
            # Ensure game is in Spectator mode
            spawn_ini_path = os.path.join(app_state.game_path, 'spawn.ini')
            config = configparser.ConfigParser()
            try:
                config.read(spawn_ini_path)
            except (FileNotFoundError, configparser.Error) as e:
                logging.error(
                    f"Failed to read configuration file {spawn_ini_path}: {e}")  # <-- this line changed to log error
                QMessageBox.critical(None, "Configuration Error",
                                     f"Failed to load game files. Please check the game path.")  # <-- this line changed to alert user
                return

            is_spectator = config.get('Settings', 'IsSpectator', fallback='False').lower() in ['true', 'yes']
            if not is_spectator:
                QMessageBox.warning(None, "Spectator Mode Required",
                                    "You can only use the Unit counter in Spectator mode.")
                return

        # Close existing HUD windows before creating new ones
        self._close_existing_hud_windows()

        if not app_state.players:
            logging.info("No valid players found. HUD will not be displayed.")
            return

        # Create resource windows for each player
        for player in app_state.players:
            logging.info(f"Creating HUD for {player.username.value} with color {player.color_name}")
            resource_window = ResourceWindow(player, len(app_state.players), settings, player.color_name)
            self.HUDs_list.append((None, resource_window))  # Unit window will be set later

        # Create unit windows according to the current mode
        self.create_unit_windows_in_current_mode()

    def _close_existing_hud_windows(self):
        """Closes any currently open HUD windows, preparing for new HUD creation."""
        for unit_window, resource_window in self.HUDs_list:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.close()
                else:
                    unit_window.close()
            # Close each individual resource window
            for window in resource_window.windows:
                window.close()
        self.HUDs_list.clear()

    # HUD Update Logic
    # ------------------------------------------------------------------------

    def update_huds(self):
        """Updates all HUDs with the latest player data, refreshing unit and resource windows."""
        if not self.HUDs_list:
            return  # No HUDs to update
        try:
            for unit_window, resource_window in self.HUDs_list:
                # Update unit window labels
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.update_labels()
                    else:
                        unit_window.update_labels()
                # Update resource window labels
                resource_window.update_labels()
        except Exception as e:
            logging.error(f"Exception in update_huds: {e}")
            traceback.print_exc()

    # HUD Window Creation in Different Modes
    # ------------------------------------------------------------------------

    def create_unit_windows_in_current_mode(self):
        """Creates unit windows for each player based on the current mode: separate or combined unit counters."""
        separate = settings.positions.get('separate_unit_counters', False)

        for i, (unit_window, resource_window) in enumerate(self.HUDs_list):
            player = resource_window.player

            # Close existing unit window using helper function
            self._close_unit_window(unit_window)

            # Create new unit windows based on the mode
            if separate:
                # Separate mode: create separate windows for images and numbers
                unit_window_images = UnitWindowImagesOnly(player, settings, selected_units)
                unit_window_images.setWindowTitle(f"Player {player.color_name} unit images window")

                unit_window_numbers = UnitWindowNumbersOnly(player, settings, selected_units)
                unit_window_numbers.setWindowTitle(f"Player {player.color_name} unit numbers window")

                self.HUDs_list[i] = ((unit_window_images, unit_window_numbers), resource_window)
            else:
                # Combined mode: create a single window with images
                unit_window = UnitWindowWithImages(player, settings, selected_units)
                unit_window.setWindowTitle(f"Player {player.color_name} unit window")

                self.HUDs_list[i] = (unit_window, resource_window)

    def _close_unit_window(self, unit_window):
        """Closes a unit window or tuple of unit windows."""
        if unit_window:
            if isinstance(unit_window, tuple):
                for uw in unit_window:
                    uw.close()
            else:
                unit_window.close()


# Global instance of HUD for managing HUD windows
HUDs = HUD()
