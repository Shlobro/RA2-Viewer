import logging

from PySide6.QtGui import QPainter, QFont, QColor, QFontDatabase, QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt


class CounterWidgetNumberOnly(QLabel):
    def __init__(self, count, color=Qt.red, size=100, parent=None):
        super().__init__(parent)
        self.count = count
        self.color = self._convert_to_qcolor(color)  # Convert color to QColor
        self.size = size
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set the maximum number of digits you expect
        self.max_digits = 3  # Adjust this based on your needs

        self.update_size(size)

    def compute_fixed_width(self):
        # Create a QFont with the desired size
        font_size = self.size  # Use the size as font size
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            self.number_font = QFont(font_family[0], font_size, QFont.Bold)
        else:
            self.number_font = QFont("Arial", font_size, QFont.Bold)

        # Use QFontMetrics to compute the width of the maximum number
        fm = QFontMetrics(self.number_font)
        max_number = '8' * self.max_digits  # Use '8's since they are typically the widest digit
        self.fixed_width = fm.horizontalAdvance(max_number)
        self.fixed_height = fm.height()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Use the font we created earlier
        painter.setFont(self.number_font)

        # Calculate text size
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(str(self.count))
        text_height = text_metrics.height()
        self.setFixedSize(self.fixed_width, self.fixed_height)

        # Calculate text position to center it
        text_x = (self.fixed_width - text_width) / 2
        text_y = self.fixed_height - text_metrics.descent()

        # Draw the black outline for the text
        painter.setPen(Qt.black)  # Outline color
        outline_thickness = 1  # Adjust as needed
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(int(text_x + dx), int(text_y + dy), str(self.count))

        # Draw the white text on top
        painter.setPen(Qt.white)
        painter.drawText(int(text_x), int(text_y), str(self.count))

    def update_count(self, new_count):
        self.count = new_count
        self.repaint()  # Redraw the widget with the updated count

    def update_size(self, new_size):
        """Dynamically update the font size."""
        self.size = new_size
        self.compute_fixed_width()
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