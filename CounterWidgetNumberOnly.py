import logging

from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt

class CounterWidget(QLabel):
    def __init__(self, count, color=Qt.red, size=100, parent=None):
        super().__init__(parent)
        self.count = count
        self.color = self._convert_to_qcolor(color)  # Convert color to QColor
        self.size = size
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.update_size(size)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Set the font for the text
        font_size = self.size  # Use the size as font size
        painter.setFont(QFont("Arial", font_size, QFont.Bold))

        # Calculate text size
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(str(self.count))
        text_height = text_metrics.height()
        self.setFixedSize(text_width, text_height)

        # Calculate text position
        text_x = 0
        text_y = text_height - text_metrics.descent()

        # Draw the black outline for the text
        painter.setPen(Qt.black)  # Outline color
        outline_thickness = 1  # Adjust as needed
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(text_x + dx, text_y + dy, str(self.count))

        # Draw the white text on top
        painter.setPen(Qt.white)
        painter.drawText(text_x, text_y, str(self.count))

    def update_count(self, new_count):
        self.count = new_count
        self.repaint()  # Redraw the widget with the updated count

    def update_size(self, new_size):
        """Dynamically update the font size."""
        self.size = new_size
        self.repaint()  # Force immediate redraw

    def update_color(self, new_color):
        self.color = self._convert_to_qcolor(new_color)
        self.update()  # Redraw the widget with the updated color

    def _convert_to_qcolor(self, color):
        """Helper method to convert various types of color inputs to QColor."""
        if isinstance(color, QColor):
            return color  # Already a QColor
        elif isinstance(color, tuple) and len(color) == 3:
            return QColor(*color)  # Convert RGB tuple (R, G, B) to QColor
        elif isinstance(color, str):
            if color.startswith('#'):
                return QColor(color)  # Handle hex string
            return QColor(color)  # Handle named color string
