#DataWidget.py
import logging
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class BaseDataWidget(QWidget):
    """Base widget for displaying data with optional fixed width, custom font, and dynamic updates."""

    def __init__(self, data=None, text_color=Qt.black, size=16, font=None, use_fixed_width=False, max_digits=8, parent=None):
        super().__init__(parent)
        self.size = size
        self.value = data if data is not None else 0
        self.custom_font = font if font else QFont()
        self.text_color = text_color
        self.use_fixed_width = use_fixed_width
        self.max_digits = max_digits

        # Create the main label for displaying data
        self.data_label = QLabel(str(self.value), self)
        self.data_label.setAlignment(Qt.AlignCenter if use_fixed_width else Qt.AlignLeft)
        self.data_label.setStyleSheet(f"color: {QColor(self.text_color).name()}; margin-top: -2px;")

        # Set initial font size and calculate fixed width if needed
        self.update_font_size()
        if use_fixed_width:
            self.compute_fixed_width()
            self.data_label.setFixedWidth(self.fixed_width)

        # Set up layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1)
        self.layout.addWidget(self.data_label, alignment=Qt.AlignVCenter)

    def compute_fixed_width(self):
        """Compute and set fixed width based on maximum digits and font metrics."""
        font = self.custom_font
        font.setPointSize(int(self.size * 0.6))
        fm = QFontMetrics(font)
        self.fixed_width = fm.horizontalAdvance('8' * self.max_digits)

    def update_font_size(self):
        """Update font size based on widget size for dynamic resizing."""
        font = self.custom_font
        font.setPointSize(int(self.size * 0.6))
        self.data_label.setFont(font)
        self.data_label.adjustSize()

    def update_data_size(self, new_size):
        """Adjust the widget size, font size, and label dimensions based on a new size."""
        self.size = new_size
        self.update_font_size()

        if self.use_fixed_width:
            self.compute_fixed_width()
            self.data_label.setFixedWidth(self.fixed_width)

        self.adjust_size()

    def adjust_size(self):
        """Update widget size to match data label size or fixed width."""
        total_width = self.data_label.width() + 1 if not self.use_fixed_width else self.fixed_width
        self.setFixedSize(total_width, self.data_label.height())

    def on_value_changed(self, value):
        """Handle changes to the displayed value."""
        self.value = value
        self.data_label.setText(str(int(value)))
        self.data_label.adjustSize()
        self.adjust_size()

    def update_color(self, new_text_color=None):
        """Update text color if a new color is provided."""
        if new_text_color:
            self.text_color = QColor(new_text_color)
            self.data_label.setStyleSheet(f"color: {self.text_color.name()}; margin-top: -2px;")
            self.data_label.adjustSize()
            self.adjust_size()

    def update_data(self, new_data):
        """Animate a change in data value for a smooth transition."""
        animation = QPropertyAnimation(self, b"value")
        animation.setDuration(500)
        animation.setStartValue(self.value)
        animation.setEndValue(new_data)
        animation.valueChanged.connect(self.on_value_changed)
        animation.start()


class MoneyWidget(BaseDataWidget):
    """Widget specifically for displaying monetary values."""

    def __init__(self, data=None, text_color=Qt.white, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, use_fixed_width=True, max_digits=8, parent=parent)
        self.update_data_label()

    def on_value_changed(self, value):
        self.value = value
        self.update_data_label()
        self.data_label.adjustSize()
        self.adjust_size()

    def update_data_label(self):
        """Update label text to display as currency."""
        self.data_label.setText(f"${int(self.value)}")


class PowerWidget(BaseDataWidget):
    """Widget for displaying power values with an optional image icon."""

    def __init__(self, data=None, image_path='bolt.png', image_color=Qt.green, text_color=Qt.green, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, use_fixed_width=False, parent=parent)
        self.image_path = image_path
        self.image_color = image_color

        # Set up the icon and add it to layout
        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)
        self.data_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.update_font_size()
        self.adjust_size()

    def load_and_set_image(self):
        """Load and colorize the icon image."""
        pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        colored_pixmap = self.colorize_pixmap(pixmap, self.image_color)
        self.icon_label.setPixmap(colored_pixmap)
        self.icon_label.setFixedSize(colored_pixmap.size())

    def colorize_pixmap(self, pixmap, color):
        """Colorize a pixmap with a given color."""
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.transparent)
        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QColor(color))
        painter.end()
        return colored_pixmap

    def update_data_size(self, new_size):
        """Adjust both text and image size."""
        self.size = new_size
        self.load_and_set_image()
        self.update_font_size()
        self.adjust_size()

    def adjust_size(self):
        """Resize widget based on text and icon dimensions."""
        total_width = self.icon_label.width() + self.data_label.width()
        total_height = max(self.icon_label.height(), self.data_label.height())
        self.setFixedSize(total_width, total_height)

    def update_color(self, new_image_color=None, new_text_color=None):
        """Update color of both text and image."""
        if new_image_color:
            self.image_color = QColor(new_image_color)
            self.load_and_set_image()
        super().update_color(new_text_color=new_text_color)


class NameWidget(BaseDataWidget):
    """Widget for displaying a name with an optional icon image."""

    def __init__(self, data=None, image_path=None, image_color=None, text_color=Qt.black, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, parent=parent)
        self.image_path = image_path
        self.image_color = image_color

        if self.image_path:
            # Set up the icon and add it to layout
            self.icon_label = QLabel(self)
            self.load_and_set_image()
            self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)

        self.update_font_size()

    def load_and_set_image(self):
        """Load and colorize the icon image if an image path is set."""
        pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.image_color:
            pixmap = self.colorize_pixmap(pixmap, self.image_color)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(pixmap.size())

    def update_data_size(self, new_size):
        """Adjust text and image sizes based on a new widget size."""
        self.size = new_size
        if self.image_path:
            self.load_and_set_image()
        self.update_font_size()
        self.adjust_size()

    def adjust_size(self):
        """Resize widget based on text and icon dimensions."""
        if self.image_path:
            total_width = self.icon_label.width() + self.data_label.width() + 1
            total_height = max(self.icon_label.height(), self.data_label.height())
            self.setFixedSize(total_width, total_height)
        else:
            super().adjust_size()


class FlagWidget(QWidget):
    """Widget for displaying a flag icon with adjustable size."""

    def __init__(self, image_path=None, size=16, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.size = size

        # Set up layout and add icon
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)

        self.adjust_size()

    def load_and_set_image(self):
        """Load the flag image and scale to widget size."""
        pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(pixmap.size())

    def update_data_size(self, new_size):
        """Update the flag image size based on a new widget size."""
        self.size = new_size
        self.load_and_set_image()
        self.adjust_size()

    def adjust_size(self):
        """Resize widget based on the icon dimensions."""
        self.setFixedSize(self.icon_label.width(), self.icon_label.height())
