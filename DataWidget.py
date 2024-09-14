from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

class DataWidget(QWidget):
    def __init__(self, image_path, data, image_color=None, text_color=Qt.black, size=16, font=None, parent=None):
        super().__init__(parent)
        self.size = size
        self.image_path = image_path
        self.image_color = image_color

        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(1)  # Reduce the space between the image and text

        # Create QLabel for the image
        self.icon_label = QLabel(self)
        pixmap = QPixmap(image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Apply the image color if provided
        if image_color:
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.transparent)
            painter = QPainter(colored_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(colored_pixmap.rect(), QColor(image_color))
            painter.end()
            pixmap = colored_pixmap

        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(pixmap.size())
        layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)

        # Create QLabel for the data (number)
        self.data_label = QLabel(str(data), self)
        self.data_label.setStyleSheet(f"color: {QColor(text_color).name()}; margin-top: -2px;")  # Move text slightly higher

        # Apply the custom font if provided, otherwise use the default font
        self.custom_font = font if font else QFont()

        layout.addWidget(self.data_label, alignment=Qt.AlignVCenter)

        # Apply the custom font or dynamically adjust the font size
        self.update_font_size()

    def update_data_size(self, new_size):
        """Reload the icon from the stored file path, apply the color, and adjust the text size."""
        self.size = new_size

        # Reload the image from the original file path
        original_pixmap = QPixmap(self.image_path)
        if original_pixmap:
            # Apply the image color before scaling, if provided
            if self.image_color is not None:
                colored_pixmap = QPixmap(original_pixmap.size())
                colored_pixmap.fill(Qt.transparent)
                painter = QPainter(colored_pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.drawPixmap(0, 0, original_pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(colored_pixmap.rect(), QColor(self.image_color))
                painter.end()
                original_pixmap = colored_pixmap

            # Rescale the colored image (or original image if no color) to the new size
            scaled_pixmap = original_pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Set the resized (and possibly recolored) pixmap to the label
            self.icon_label.setPixmap(scaled_pixmap)
            self.icon_label.setFixedSize(scaled_pixmap.size())

        # Update the font size based on the new size
        self.update_font_size()

        # Recalculate the widget size after resizing
        self.adjust_size()

    def update_font_size(self):
        """Dynamically resize the font based on the image size, even with custom fonts."""
        # Adjust the point size proportionally to the widget size
        font = self.custom_font
        font.setPointSize(int(self.size * 0.6))  # Adjust font size proportionally to image size
        self.data_label.setFont(font)
        self.data_label.adjustSize()

    def update_data(self, new_data):
        """Update the data shown in the widget."""
        self.data_label.setText(str(new_data))
        self.data_label.adjustSize()
        self.adjust_size()

    def adjust_size(self):
        """Recalculate the widget size based on the image and text."""
        self.setFixedSize(self.icon_label.width() + self.data_label.width() + 1, max(self.icon_label.height(), self.data_label.height()))

    def update_color(self, new_image_color=None, new_text_color=None):
        """Update the color of the image and the text."""

        # Update the image color if a new one is provided
        if new_image_color is not None:
            self.image_color = new_image_color

            # Reload the image with the new color
            pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

        # Update the text color if a new one is provided
        if new_text_color is not None:
            self.data_label.setStyleSheet(f"color: {QColor(new_text_color).name()}; margin-top: -2px;")
            self.data_label.adjustSize()

        # Recalculate the widget size after recoloring
        self.adjust_size()
