from PySide6.QtGui import QPixmap, QPainter, QFont, QPen, QColor
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt

class CounterWidget(QLabel):
    def __init__(self, count, image_path, color=Qt.red, size=100, parent=None):
        super().__init__(parent)
        self.count = count
        self.image_path = image_path
        self.color = self._convert_to_qcolor(color)  # Convert color to QColor
        self.size = size
        self.setFixedSize(size, size)  # Fixed size for the image and count display

        # Set size policy to ensure tight-fitting
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Load the image and ensure it keeps its aspect ratio
        pixmap = QPixmap(self.image_path)

        # Calculate the scaled pixmap with aspect ratio maintained
        scaled_pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Get the actual size of the scaled pixmap
        scaled_width = scaled_pixmap.width()
        scaled_height = scaled_pixmap.height()

        # Calculate where to draw the image within the widget (center the image)
        x_offset = (self.width() - scaled_width) // 2  # Use self.width() instead of fixed size
        y_offset = (self.height() - scaled_height) // 2  # Use self.height() instead of fixed size

        # Draw the image
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

        # Set the font for the text (scaling based on size)
        painter.setFont(QFont("Arial", int(self.size / 5), QFont.Bold))

        # Draw the black outline by slightly offsetting the text in multiple directions
        painter.setPen(Qt.black)  # Set the pen to black for the outline
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            painter.drawText(self.rect().adjusted(dx, dy, dx, dy), Qt.AlignCenter, str(self.count))

        # Draw the white text on top
        painter.setPen(Qt.white)  # Set white text color
        painter.drawText(self.rect(), Qt.AlignCenter, str(self.count))  # Draw the actual text

        # Draw the rounded colored frame around the scaled image
        pen = QPen(self.color)  # Use the passed color for the frame
        pen.setWidth(int(self.size / 25))  # Set the width of the frame
        painter.setPen(pen)

        # Draw a rounded rectangle around the actual image size
        radius = min(scaled_width, scaled_height) / 8  # Adjust radius for the rounded corners
        painter.drawRoundedRect(x_offset, y_offset, scaled_width, scaled_height, radius,
                                radius)  # Draw the rounded rectangle

    def update_count(self, new_count):
        self.count = new_count
        self.update()  # Redraw the widget with the updated count

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
                return QColor(color)  # Handle hex string (e.g., '#
