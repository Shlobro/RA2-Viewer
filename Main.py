import json
import os
import threading
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QVBoxLayout, QMainWindow, QLabel, QSpinBox

from DataTracker import ResourceWindow
from Player import Player
from UnitCounter import UnitWindow
from UnitSelectionWindow import UnitSelectionWindow

# Global variable for player count (default 2 players)
player_count = 2
hud_position_file = 'hud_positions.json'

# List to store player objects
players = []
hud_windows = []  # List to store HUDWindow objects


# Update the create_hud_windows function to create both Unit and Resource windows
def create_hud_windows():
    global hud_windows
    for player in players:
        unit_window = UnitWindow(player, player_count, hud_positions)
        resource_window = ResourceWindow(player, player_count, hud_positions)
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


# Store the HUD positions in memory
hud_positions = load_hud_positions()


# Create Player objects based on player count
def create_players():
    global players
    players = [Player(i + 1) for i in range(player_count)]


# Function to update both Unit and Resource HUDs with player data
def update_huds():
    for unit_window, resource_window in hud_windows:
        unit_window.update_labels()  # Update the unit count (e.g., Rhino tanks)
        resource_window.update_labels()  # Update money and power


# Background thread to continuously update player data
def continuous_data_update():
    while True:
        for player in players:
            player.update_data()
        time.sleep(1)


# Function to toggle HUD visibility (show/hide all HUDs)
hud_visible = True


def toggle_huds():
    global hud_visible
    hud_visible = not hud_visible
    for unit_window, resource_window in hud_windows:
        if hud_visible:
            unit_window.show()  # Show the UnitWindow
            resource_window.show()  # Show the ResourceWindow
            toggle_button.setText("Hide Data")  # Change button text to "Hide Data"
        else:
            unit_window.hide()  # Hide the UnitWindow
            resource_window.hide()  # Hide the ResourceWindow
            toggle_button.setText("Show Data")  # Change button text to "Show Data"


# Handle closing the application
def on_closing():
    save_hud_positions()
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
        self.data_size_label = QLabel("Set Data Window Size: (10 - 50)")
        layout.addWidget(self.data_size_label)

        data_size = hud_positions.get('data_counter_size', 16)  # Default to 16 for data windows
        self.data_size_spinbox = QSpinBox()
        self.data_size_spinbox.setRange(10, 50)
        self.data_size_spinbox.setValue(data_size)
        self.data_size_spinbox.valueChanged.connect(self.update_data_window_size)  # Correct method call
        layout.addWidget(self.data_size_spinbox)

        global toggle_button
        toggle_button = QPushButton("Hide Data")
        toggle_button.clicked.connect(toggle_huds)
        layout.addWidget(toggle_button)

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
        for unit_window, _ in hud_windows:
            unit_window.update_all_counters_size(new_size)
        hud_positions['unit_counter_size'] = new_size

    def update_data_window_size(self):
        new_size = self.data_size_spinbox.value()
        for _, resource_window in hud_windows:  # Loop through resource windows
            resource_window.update_all_data_size(new_size)  # Ensure resource windows are updated correctly
        hud_positions['data_counter_size'] = new_size  # Consistent naming in hud_positions

    # Method to open the Unit Selection window and keep it open
    def open_unit_selection(self):
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow('unit_selection.json')
            self.unit_selection_window.show()

    # Method to toggle the visibility of Money
    def toggle_money(self, state):
        for _, resource_window in hud_windows:
            if state == 2:
                resource_window.money_widget.show()
            else:
                resource_window.money_widget.hide()

    # Method to toggle the visibility of Power
    def toggle_power(self, state):
        for _, resource_window in hud_windows:
            if state == 2:
                resource_window.power_widget.show()
            else:
                resource_window.power_widget.hide()



# Main application loop
if __name__ == '__main__':
    app = QApplication([])

    control_panel = ControlPanel()
    control_panel.show()

    create_players()
    create_hud_windows()

    # Start the background thread to update player data
    thread = threading.Thread(target=continuous_data_update, daemon=True)
    thread.start()

    # Start a timer to periodically update the HUDs
    timer = QTimer()
    timer.timeout.connect(update_huds)
    timer.start(1000)

    # Run the application's event loop
    app.exec()

    # Save HUD positions on exit
    save_hud_positions()
