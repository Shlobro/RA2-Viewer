import logging

from PySide6.QtGui import QPixmap, QPainter, QFont, QPen, QColor
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QRect

class CounterWidget(QLabel):
    def __init__(self, image_path, color=Qt.red, size=100, show_frame=True, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.color = self._convert_to_qcolor(color)  # Convert color to QColor
        self.size = size
        self.show_frame = show_frame  # New attribute to control frame visibility
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Load the image and scale it dynamically
        self.update_image_size()

    def update_image_size(self):
        """Dynamically load and scale the image based on the desired size."""
        pixmap = QPixmap(self.image_path)
        self.scaled_pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setFixedSize(self.scaled_pixmap.size())  # Adjust widget size to match the image

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the image
        painter.drawPixmap(0, 0, self.scaled_pixmap)

        # Set the font for the text to take about 1/4th of the widget
        font_size = int(self.size / 3)  # Text should take up about 25% of the widget
        painter.setFont(QFont("Arial", font_size, QFont.Bold))

        # Define dynamic padding based on widget size
        padding_x = max(5, int(self.size * 0.05))  # Slightly larger padding for bigger widgets
        padding_y = max(5, int(self.size * 0.05))  # Slightly larger padding for bigger widgets


        # Draw the colored frame around the image if show_frame is True
        if self.show_frame:
            pen = QPen(self.color)
            pen.setWidth(int(self.size / 15))  # Set the width of the frame
            painter.setPen(pen)

            # Draw a rounded rectangle around the image
            painter.drawRoundedRect(0, 0, self.scaled_pixmap.width(), self.scaled_pixmap.height(), 10, 10)

    def update_show_frame(self, show_frame):
        """Update the visibility of the frame."""
        self.show_frame = show_frame
        self.repaint()  # Force immediate redraw

    def update_count(self, new_count):
        self.count = new_count
        self.repaint()  # Redraw the widget with the updated count

    def update_size(self, new_size):
        """Dynamically update the widget and image size."""
        self.size = new_size
        self.update_image_size()
        self.repaint()  # Force immediate redraw

    def update_color(self, new_color):
        self.color = QColor(new_color)
        self.update()  # Redraw the widget with the updated color

    def _convert_to_qcolor(self, color):
        """
        Helper method to convert various types of color inputs to QColor.
        Handles QColor, RGB tuple, hex strings, or named color strings.
        """
        if isinstance(color, QColor):
            return color  # Already a QColor
        elif isinstance(color, tuple) and len(color) == 3:
            return QColor(*color)  # Convert RGB tuple (R, G, B) to QColor
        elif isinstance(color, str):
            if color.startswith('#'):
                return QColor(color)  # Handle hex string (e.g., '#000000')
