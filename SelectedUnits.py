# SelectedUnits.py
import json
import logging
import os


class SelectedUnits:
    """Manages selection, storage, and retrieval of game units, organized by name, faction, and type."""

    def __init__(self):
        # Filename for saving and loading selected units data
        self.selected_units_file_name = 'unit_selection.json'

        # Dictionaries to organize selected units
        self.selected_units_dict = {}  # Primary storage for all selected units
        self.units_by_name = {}  # Lookup dictionary for units by name
        self.units_by_faction = {}  # Lookup dictionary for units by faction
        self.units_by_unit_type = {}  # Lookup dictionary for units by type

    def save_selected_units(self):
        """Saves the current selected units to a JSON file."""
        try:
            with open(self.selected_units_file_name, 'w') as file:
                json.dump(self.selected_units_dict, file, indent=4)
            logging.info("Selected units saved successfully.")
        except Exception as e:
            logging.error(f"Error saving selected units: {e}")

    def load_selected_units(self):
        """Loads selected units from a JSON file, populating dictionaries for quick access by name, faction, and type."""

        # Check if the selection file exists; if not, initialize an empty structure
        if os.path.exists(self.selected_units_file_name):
            try:
                with open(self.selected_units_file_name, 'r') as file:
                    data = json.load(file)
                    self.selected_units_dict = data.get('selected_units', {})
            except json.JSONDecodeError as e:
                logging.error(f"Error loading selected units: {e}")
                self.selected_units_dict = {'selected_units': {}}
        else:
            self.selected_units_dict = {'selected_units': {}}

        # Populate lookup dictionaries for quick access by unit attributes
        for faction, unit_types in self.selected_units_dict.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    self.units_by_name[unit_name] = unit_info
                    self.units_by_faction[unit_name] = faction
                    self.units_by_unit_type[unit_name] = unit_type


# Create an instance for use in the application
selected_units = SelectedUnits()
