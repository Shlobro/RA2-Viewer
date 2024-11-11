# AppState.py

import threading

class AppState:
    """Maintains the state of the application, including player data, threading locks, and application configuration."""

    def __init__(self):
        # Attributes for managing the game's state and configurations
        self.players = []                     # List to store active player instances
        self.data_lock = threading.Lock()      # Thread lock for safe data access
        self.process_handle = None             # Handle for the game process (if applicable)
        self.game_path = ''                    # Path to the game executable
        self.control_panel = None              # Reference to the control panel UI component
        self.data_update_thread = None         # Background thread for updating data
        self.admin = False                     # Flag for administrative privileges, if needed

    def add_player(self, player):
        """Adds a player instance to the players list."""
        self.players.append(player)

    def update_all_players(self):
        """Calls update_dynamic_data on each player instance, updating game state information."""
        for player in self.players:
            player.update_dynamic_data()


# Global instance of AppState for application-wide use
app_state = AppState()
