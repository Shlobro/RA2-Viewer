# unit_data.py

import json
import logging
import os


class UnitData:
    """Manages loading, saving, and organizing data on selected units by faction and type."""

    def __init__(self):
        # Dictionaries to store selected unit data
        self.selected_units = {}  # Full data on selected units
        self.unit_info_by_name = {}  # Lookup table for unit info by name
        self.unit_to_faction = {}  # Maps unit name to faction
        self.unit_to_unit_type = {}  # Maps unit name to unit type

        # Load unit selections from file
        self.load_selected_units()

    # Load and Initialize Selected Units
    # ------------------------------------------------------------------------

    def load_selected_units(self):
        """Loads selected units from JSON file, initializing dictionaries for quick access."""
        json_file = 'unit_selection.json'

        # Check if the JSON file exists
        if os.path.exists(json_file):
            with open(json_file, 'r') as file:
                data = json.load(file)
                self.selected_units = data.get('selected_units', {})
        else:
            self.selected_units = {}
            logging.warning("unit_selection.json not found. Starting with empty selection.")

        # Validate the structure of loaded data
        if not isinstance(self.selected_units, dict):
            logging.error("Invalid data structure in unit_selection.json. Expected a dictionary.")
            self.selected_units = {}

        # Populate lookup dictionaries with the selected units data
        self._populate_unit_lookup_tables()

    def _populate_unit_lookup_tables(self):
        """Populates lookup tables for unit information, organized by name, faction, and type."""
        for faction, unit_types in self.selected_units.items():
            if not isinstance(unit_types, dict):
                logging.error(f"Invalid structure for faction '{faction}': expected a dictionary.")
                continue
            for unit_type, units in unit_types.items():
                if not isinstance(units, dict):
                    logging.error(
                        f"Invalid structure for unit type '{unit_type}' under faction '{faction}': expected a dictionary.")
                    continue
                for unit_name, unit_info in units.items():
                    self.unit_info_by_name[unit_name] = unit_info
                    self.unit_to_faction[unit_name] = faction
                    self.unit_to_unit_type[unit_name] = unit_type

    # Save Selected Units
    # ------------------------------------------------------------------------

    def save_selected_units(self):
        """Saves the current selected units to a JSON file."""
        json_file = 'unit_selection.json'
        try:
            with open(json_file, 'w') as file:
                json.dump({'selected_units': self.selected_units}, file, indent=4)
            logging.info("Selected units saved successfully.")
        except IOError as e:
            logging.error(f"Error saving selected units to {json_file}: {e}")


# Instantiate the UnitData class for application-wide use
unit_data = UnitData()
