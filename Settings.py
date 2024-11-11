# Settings.py

import json
import os


class Settings:
    """Manages loading, saving, and providing defaults for HUD positions and settings."""

    def __init__(self):
        # Filename for saving and loading HUD settings
        self.hud_positions_filename = 'hud_positions.json'

        # Load or initialize HUD settings
        self.positions = self.load_hud_positions()

    # Load and Initialize HUD Positions
    # ------------------------------------------------------------------------

    def load_hud_positions(self):
        """Loads HUD positions from a JSON file, or initializes defaults if the file does not exist."""
        hud_positions = {}
        if os.path.exists(self.hud_positions_filename):
            with open(self.hud_positions_filename, 'r') as file:
                hud_positions = json.load(file)

        # Set default values if not present
        hud_positions.setdefault('unit_counter_size', 75)
        hud_positions.setdefault('image_size', 75)
        hud_positions.setdefault('number_size', 75)
        hud_positions.setdefault('distance_between_numbers', 0)
        hud_positions.setdefault('show_name', True)
        hud_positions.setdefault('show_money', True)
        hud_positions.setdefault('show_power', True)
        hud_positions.setdefault('unit_layout', 'Vertical')  # Default layout orientation
        hud_positions.setdefault('money_color', 'Use player color')
        hud_positions.setdefault('show_flag', True)
        hud_positions.setdefault('flag_widget_size', 50)
        hud_positions.setdefault('show_unit_frames', True)
        hud_positions.setdefault('name_widget_size', 50)
        hud_positions.setdefault('money_widget_size', 50)
        hud_positions.setdefault('power_widget_size', 50)
        hud_positions.setdefault('separate_unit_counters', False)

        return hud_positions

    # Save HUD Positions and Settings
    # ------------------------------------------------------------------------

    def save_hud_positions(self, app_state):
        """Saves current HUD settings and positions to a JSON file."""

        control_panel = app_state.control_panel
        hud_positions = app_state.settings
        hud_windows = app_state.HUDs_list

        # Save HUD sizes from control panel spin boxes
        if control_panel:
            self._save_control_panel_settings(control_panel, hud_positions)

        # Save the game path from the QLineEdit
        if control_panel.path_edit:
            hud_positions['game_path'] = control_panel.path_edit.text()

        # Save positions of all HUD windows
        self._save_hud_window_positions(hud_windows, hud_positions)

        # Write the settings to the file
        with open(self.hud_positions_filename, 'w') as file:
            json.dump(hud_positions, file, indent=4)

    # Helper Methods for Saving Settings
    # ------------------------------------------------------------------------

    def _save_control_panel_settings(self, control_panel, hud_positions):
        """Saves settings values from control panel UI elements."""

        hud_positions['unit_counter_size'] = control_panel.counter_size_spinbox.value()
        hud_positions['image_size'] = control_panel.image_size_spinbox.value()
        hud_positions['number_size'] = control_panel.number_size_spinbox.value()
        hud_positions['distance_between_numbers'] = control_panel.distance_spinbox.value()
        hud_positions['name_widget_size'] = control_panel.name_size_spinbox.value()
        hud_positions['money_widget_size'] = control_panel.money_size_spinbox.value()
        hud_positions['power_widget_size'] = control_panel.power_size_spinbox.value()

        # Save state of checkboxes and selections
        hud_positions['show_name'] = control_panel.name_checkbox.isChecked()
        hud_positions['show_money'] = control_panel.money_checkbox.isChecked()
        hud_positions['show_power'] = control_panel.power_checkbox.isChecked()
        hud_positions['unit_layout'] = control_panel.layout_combo.currentText()
        hud_positions['show_unit_frames'] = control_panel.unit_frame_checkbox.isChecked()
        hud_positions['money_color'] = control_panel.color_combo.currentText()
        hud_positions['separate_unit_counters'] = control_panel.separate_units_checkbox.isChecked()

    def _save_hud_window_positions(self, hud_windows, hud_positions):
        """Saves positions of all HUD windows for each player."""

        for unit_window, resource_window in hud_windows:
            player_id = resource_window.player.color_name

            # Ensure the player's section exists in hud_positions
            if player_id not in hud_positions:
                hud_positions[player_id] = {}

            # Save positions for individual resource windows (name, money, power, flag)
            hud_positions[player_id]['flag'] = self._get_window_position(resource_window.windows[3])
            hud_positions[player_id]['name'] = self._get_window_position(resource_window.windows[0])
            hud_positions[player_id]['money'] = self._get_window_position(resource_window.windows[1])
            hud_positions[player_id]['power'] = self._get_window_position(resource_window.windows[2])

            # Save positions of unit windows based on mode
            if hud_positions.get('separate_unit_counters', False):
                # Separate unit counters: individual windows for images and numbers
                unit_window_images, unit_window_numbers = unit_window
                hud_positions[player_id]['unit_counter_images'] = self._get_window_position(unit_window_images)
                hud_positions[player_id]['unit_counter_numbers'] = self._get_window_position(unit_window_numbers)
            else:
                # Combined unit counter window
                hud_positions[player_id]['unit_counter_combined'] = self._get_window_position(unit_window)

    def _get_window_position(self, window):
        """Helper to return a dictionary with the x, y position of a given window."""
        return {"x": window.pos().x(), "y": window.pos().y()}


# Global instance of Settings for application-wide use
settings = Settings()
