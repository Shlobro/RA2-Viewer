# Create a separate window for displaying resources (e.g., money and power)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from DataWidget import DataWidget

faction_to_flag = {
    "British": "RA2_Flag_Britain.png",
    "Confederation": "RA2_Flag_Cuba.png",
    "Germans": "RA2_Flag_Germany.png",
    "Arabs": "RA2_Flag_Iraq.png",
    "French": "RA2_Flag_France.png",
    "Alliance": "RA2_Flag_Korea.png",
    "Africans": "RA2_Flag_Libya.png",
    "Russians": "RA2_Flag_Russia.png",
    "Americans": "RA2_Flag_USA.png",
    "YuriCountry": "RA2_Yuricountry.png"
}


class ResourceWindow(QMainWindow):
    def __init__(self, player, player_count, hud_positions):
        super().__init__()
        self.player = player

        self.size = hud_positions.get('data_counter_size', 16)  # Default size is 100 if not present

        # Get the initial position of the Resource HUD
        pos = self.get_default_position(player.index, 'resource', player_count, hud_positions)
        self.setGeometry(pos['x'], pos['y'], 250, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.make_hud_movable(player_count, hud_positions)
        self.widgetList = []

        resource_frame = QFrame(self)
        layout = QVBoxLayout(resource_frame)
        resource_frame.setLayout(layout)
        self.setCentralWidget(resource_frame)  # Ensure that the frame is the central widget

        # Create a bold, clear font for money
        money_font = QFont("Arial Black", 18, QFont.Bold)  # Larger, bold font to emphasize financial values

        # Create a modern, sleek font for power
        power_font = QFont("Impact", 18, QFont.Bold)  # Strong and bold font for power

        username_font = QFont("Roboto", 16, QFont.Bold)  # Change the font size and weight as needed

        self.name_widget = DataWidget(
            image_path="Flags/PNG/" + faction_to_flag[player.country_name.value.decode('utf-8')],
            data=self.player.username.value,
            image_color=None,
            text_color=player.color,
            size=self.size,
            font=username_font  # Apply the custom font for the username
        )
        self.widgetList.append(self.name_widget)

        # Create DataWidget for money with the custom money font
        self.money_widget = DataWidget(
            image_path='dollar.png',
            data=self.player.balance,
            image_color=Qt.green,
            text_color=Qt.green,
            size=self.size,
            font=money_font  # Apply the custom font for money
        )
        layout.addWidget(self.money_widget)
        self.widgetList.append(self.money_widget)

        # Create DataWidget for power with the custom power font
        self.power_widget = DataWidget(
            image_path='bolt.png',
            data=self.player.power,
            image_color=Qt.yellow,
            text_color=Qt.yellow,
            size=self.size,
            font=power_font  # Apply the custom font for power
        )
        self.widgetList.append(self.power_widget)



        for widget in self.widgetList:
            layout.addWidget(widget)

        self.show()

    def update_labels(self):
        # print("Updating the data Label")
        """Update the money and power values."""
        self.money_widget.update_data(self.player.balance)
        self.power_widget.update_data(self.player.power)
        if self.player.power < 0:
            self.power_widget.update_color(Qt.red, Qt.red)
        else:
            self.power_widget.update_color(Qt.yellow, Qt.yellow)

    # Other methods (make_hud_movable, get_default_position, etc.) remain the same

    def make_hud_movable(self, player_count, hud_positions):
        self.offset = None

        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None:
                x = event.globalX() - self.offset.x()
                y = event.globalY() - self.offset.y()
                self.move(x, y)
                self.update_hud_position(self.player.index, 'resource', x, y, player_count, hud_positions)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def get_default_position(self, player_id, hud_type, player_count, hud_positions):
        player_id_str = str(player_id)
        player_count_str = str(player_count)

        # Check if player_count exists, if not, create it
        if player_count_str not in hud_positions:
            hud_positions[player_count_str] = {}

        # Check if player_id exists within player_count, if not, create it
        if player_id_str not in hud_positions[player_count_str]:
            hud_positions[player_count_str][player_id_str] = {}

        # Check if hud_type exists for the player, if not, create default position for it
        if hud_type not in hud_positions[player_count_str][player_id_str]:
            # Set default x and y positions
            default_position = {"x": 100 * player_id, "y": 100 * player_id}
            hud_positions[player_count_str][player_id_str][hud_type] = default_position
        else:
            # If hud_type exists, return the stored position
            default_position = hud_positions[player_count_str][player_id_str][hud_type]

        # Return the position (either the one from JSON or the default one we created)
        return default_position

    def update_hud_position(self, player_id, hud_type, x, y, player_count, hud_positions):
        if str(player_count) not in hud_positions:
            hud_positions[str(player_count)] = {}
        if str(player_id) not in hud_positions[str(player_count)]:
            hud_positions[str(player_count)][str(player_id)] = {}
        hud_positions[str(player_count)][str(player_id)][hud_type] = {"x": x, "y": y}

    def update_all_data_size(self, new_size):
        """Resize all DataWidgets in this ResourceWindow."""
        for widget in self.widgetList:
            widget.update_data_size(new_size)

        # Ensure the window resizes accordingly
        self.setFixedSize(self.sizeHint())  # Update the window size
