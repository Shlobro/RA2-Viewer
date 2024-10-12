# Create a separate window for displaying resources (e.g., money and power)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QFontDatabase
from PySide6.QtWidgets import QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
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
    def __init__(self, player, player_count, hud_positions, player_index):
        super().__init__()
        self.player = player

        self.size = hud_positions.get('data_counter_size', 16)  # Default size is 100 if not present

        # Get the initial position of the Resource HUD
        pos = self.get_default_position(self.player.color_name, 'resource', player_count, hud_positions)
        self.setGeometry(pos['x'], pos['y'], 250, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.make_hud_movable(player_count, hud_positions)
        self.widgetList = []

        resource_frame = QFrame(self)
        layout = QVBoxLayout(resource_frame)
        resource_frame.setLayout(layout)
        self.setCentralWidget(resource_frame)  # Ensure that the frame is the central widget

        # Load the font from a file
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)

        # Check if the font was loaded successfully and apply it
        if font_family:
            money_font = QFont(font_family[0], 18, QFont.Bold)  # Set the size and weight
        else:
            money_font = QFont("Arial", 18, QFont.Bold)

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
            image_color=Qt.white,
            text_color=Qt.white,
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

        # TODO: make an if condition according to Main.py separate button
        # Create a window for the name widget
        name_window = self.create_window_with_widget(f"Player {player_index} Name", self.name_widget, player_count, hud_positions, 'name', player_index)
        if hud_positions['show_name']:
            name_window.show()
        else:
            name_window.hide()
        # Create a window for the money widget
        money_window = self.create_window_with_widget(f"Player {player_index} money", self.money_widget, player_count, hud_positions, 'money', player_index)
        if hud_positions['show_money']:
            money_window.show()
        else:
            money_window.hide()
        # Create a window for the power widget
        power_window = self.create_window_with_widget(f"Player {player_index} power", self.power_widget, player_count, hud_positions, 'power', player_index)
        if hud_positions['show_power']:
            power_window.show()
        else:
            power_window.hide()

        self.windows = [name_window, money_window, power_window]

        self.show()

    # Function to create a new window with a widget
    def create_window_with_widget(self, title, widget, player_count, hud_positions ,hud_type, player_id):
        """Create a new window for a given widget with a specified title."""
        window = QWidget()
        window.setWindowTitle(title)
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        window.setAttribute(Qt.WA_TranslucentBackground)

        # Get the initial position of the HUD
        pos = self.get_default_position(player_id, hud_type, player_count, hud_positions)
        window.setGeometry(pos['x'], pos['y'], widget.sizeHint().width(), widget.sizeHint().height())

        # Create layout and add widget
        layout = QVBoxLayout()
        layout.addWidget(widget)
        window.setLayout(layout)

        # Implement movable functionality
        offset = None

        def mouse_press_event(event):
            nonlocal offset
            if event.button() == Qt.LeftButton:
                offset = event.pos()

        def mouse_move_event(event):
            if offset is not None:
                x = event.globalX() - offset.x()
                y = event.globalY() - offset.y()
                window.move(x, y)
                self.update_hud_position(player_id, hud_type, x, y, player_count, hud_positions)

        window.mousePressEvent = mouse_press_event
        window.mouseMoveEvent = mouse_move_event

        window.show()  # Show the window immediately
        return window

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
                self.update_hud_position(self.player.color_name, 'resource', x, y, player_count, hud_positions)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def get_default_position(self, player_color, hud_type, player_count, hud_positions):
        player_color_str = player_color  # Use player's color as the key

        # Ensure the player's color section exists in hud_positions
        if player_color_str not in hud_positions:
            hud_positions[player_color_str] = {}

        # Check if hud_type exists for the player, if not, create default position for it
        if hud_type not in hud_positions[player_color_str]:
            # Set default x and y positions
            default_position = {"x": 100, "y": 100}
            hud_positions[player_color_str][hud_type] = default_position
        else:
            default_position = hud_positions[player_color_str][hud_type]

        # Ensure the position values are integers
        default_position['x'] = int(default_position['x'])
        default_position['y'] = int(default_position['y'])

        return default_position

    def update_hud_position(self, player_color, hud_type, x, y, player_count, hud_positions):
        player_color_str = player_color  # Use player's color as the key

        # Ensure the player's color section exists in hud_positions
        if player_color_str not in hud_positions:
            hud_positions[player_color_str] = {}

        # Update the HUD position for this player and type
        hud_positions[player_color_str][hud_type] = {"x": x, "y": y}

    def update_all_data_size(self, new_size):
        """Resize all DataWidgets in this ResourceWindow."""
        for widget in self.widgetList:
            widget.update_data_size(new_size)

        # Ensure the window resizes accordingly
        self.setFixedSize(self.sizeHint())  # Update the window size
