import logging

from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

class BaseDataWidget(QWidget):
    def __init__(self, data=None, text_color=Qt.black, size=16, font=None, parent=None):
        super().__init__(parent)
        self.size = size
        self.value = data if data is not None else 0
        self.custom_font = font if font else QFont()
        self.text_color = text_color

        # Create the layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setSpacing(1)  # Reduce the space between elements

        # Create QLabel for the data (text or number)
        self.data_label = QLabel(str(self.value), self)
        self.data_label.setStyleSheet(f"color: {QColor(self.text_color).name()}; margin-top: -2px;")  # Adjust text position

        self.layout.addWidget(self.data_label, alignment=Qt.AlignVCenter)

        # Apply the custom font or dynamically adjust the font size
        self.update_font_size()

    def update_data_size(self, new_size):
        """Adjust the text size."""
        self.size = new_size

        # Update the font size based on the new size
        self.update_font_size()

        # Recalculate the widget size after resizing
        self.adjust_size()

    def adjust_size(self):
        """Recalculate the widget size based on the image and text."""
        self.setFixedSize(self.data_label.width() + 1, self.data_label.height())

    def update_font_size(self):
        """Dynamically resize the font based on the image size, even with custom fonts."""
        # Adjust the point size proportionally to the widget size
        font = self.custom_font
        font.setPointSize(int(self.size * 0.6))  # Adjust font size proportionally to image size
        self.data_label.setFont(font)
        self.data_label.adjustSize()

    def update_data(self, new_data):
        """Smoothly update the data using QPropertyAnimation."""
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.value)
        self.animation.setEndValue(new_data)
        self.animation.valueChanged.connect(self.on_value_changed)
        self.animation.start()

    def on_value_changed(self, value):
        self.value = value
        self.data_label.setText(str(int(value)))  # Display integer for a clean update
        self.data_label.adjustSize()
        self.adjust_size()

    def update_color(self, new_text_color=None):
        """Update the color of the text."""
        if new_text_color is not None:
            self.text_color = QColor(new_text_color)
            logging.debug(f"update_color called with new_text_color: {self.text_color.name()}")
            self.data_label.setStyleSheet(f"color: {self.text_color.name()}; margin-top: -2px;")
            self.data_label.adjustSize()
            self.adjust_size()


class MoneyWidget(BaseDataWidget):
    def __init__(self, data=None, text_color=Qt.white, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, parent=parent)
        self.update_data_label()

    def on_value_changed(self, value):
        self.value = value
        self.update_data_label()
        self.data_label.adjustSize()
        self.adjust_size()

    def update_data_label(self):
        self.data_label.setText(f"${int(self.value)}")

class PowerWidget(BaseDataWidget):
    def __init__(self, data=None, image_path='bolt.png', image_color=Qt.green, text_color=Qt.green, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, parent=parent)
        self.image_path = image_path
        self.image_color = image_color

        # Load and set the image
        self.icon_label = QLabel(self)
        self.load_and_set_image()

        # Insert the icon_label before the data_label
        self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)

        self.update_font_size()

    def load_and_set_image(self):
        pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Apply the image color
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.transparent)
        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QColor(self.image_color))
        painter.end()
        self.icon_label.setPixmap(colored_pixmap)
        self.icon_label.setFixedSize(colored_pixmap.size())

    def update_data_size(self, new_size):
        """Adjust the text size and image size."""
        self.size = new_size
        self.load_and_set_image()
        self.update_font_size()
        self.adjust_size()

    def adjust_size(self):
        """Recalculate the widget size based on the image and text."""
        self.setFixedSize(self.icon_label.width() + self.data_label.width() + 1, max(self.icon_label.height(), self.data_label.height()))

    def update_color(self, new_image_color=None, new_text_color=None):
        """Update the color of the image and the text."""
        # Update the image color if a new one is provided
        if new_image_color is not None:
            self.image_color = QColor(new_image_color)
            self.load_and_set_image()

        # Update the text color using the method from the base class
        super().update_color(new_text_color=new_text_color)


class NameWidget(BaseDataWidget):
    def __init__(self, data=None, image_path=None, image_color=None, text_color=Qt.black, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, parent=parent)
        self.image_path = image_path
        self.image_color = image_color

        if self.image_path:
            # Load and set the image
            self.icon_label = QLabel(self)
            self.load_and_set_image()
            # Insert the icon_label before the data_label
            self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)

        self.update_font_size()

    def load_and_set_image(self):
        pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.image_color is not None:
            # Apply the image color
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.transparent)
            painter = QPainter(colored_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(colored_pixmap.rect(), QColor(self.image_color))
            painter.end()
            pixmap = colored_pixmap  # Use the colored pixmap
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(pixmap.size())

    def update_data_size(self, new_size):
        """Adjust the text size and image size."""
        self.size = new_size
        if self.image_path:
            self.load_and_set_image()
        self.update_font_size()
        self.adjust_size()

    def adjust_size(self):
        """Recalculate the widget size based on the image and text."""
        if self.image_path:
            self.setFixedSize(self.icon_label.width() + self.data_label.width() + 1, max(self.icon_label.height(), self.data_label.height()))
        else:
            super().adjust_size()
class FlagWidget(QWidget):
    def __init__(self, image_path=None, size=16, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.size = size

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)

        self.adjust_size()

    def load_and_set_image(self):
        pixmap = QPixmap(self.image_path).scaled(
            self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(pixmap.size())

    def update_data_size(self, new_size):
        """Adjust the image size."""
        self.size = new_size
        self.load_and_set_image()
        self.adjust_size()

    def adjust_size(self):
        """Recalculate the widget size based on the image."""
        self.setFixedSize(self.icon_label.width(), self.icon_label.height())