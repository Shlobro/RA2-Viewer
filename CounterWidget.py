from PySide6.QtGui import QColor, QPixmap, QPainter, QPen, QFontDatabase, QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt

class CounterWidgetBase(QLabel):
    def __init__(self, color=Qt.red, size=100, parent=None):
        super().__init__(parent)
        self.color = self._convert_to_qcolor(color)
        self.size = size
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def update_size(self, new_size):
        self.size = new_size
        self.repaint()

    def update_color(self, new_color):
        self.color = self._convert_to_qcolor(new_color)
        self.repaint()

    def update_count(self, new_count):
        self.count = new_count
        self.repaint()

    def _convert_to_qcolor(self, color):
        if isinstance(color, QColor):
            return color
        elif isinstance(color, tuple) and len(color) == 3:
            return QColor(*color)
        elif isinstance(color, str):
            if color.startswith('#'):
                return QColor(color)
            return QColor(color)
        else:
            return QColor(Qt.red)  # Default color

    def update_show_frame(self, show_frame):
        self.show_frame = show_frame
        self.repaint()

class CounterWidgetImageOnly(CounterWidgetBase):
    def __init__(self, image_path, color=Qt.red, size=100, show_frame=True, parent=None):
        super().__init__(color=color, size=size, parent=parent)
        self.image_path = image_path
        self.show_frame = show_frame
        self.update_image_size()

    def update_image_size(self):
        pixmap = QPixmap(self.image_path)
        self.scaled_pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setFixedSize(self.scaled_pixmap.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.scaled_pixmap)
        if self.show_frame:
            pen = QPen(self.color)
            pen.setWidth(int(self.size / 15))
            painter.setPen(pen)
            painter.drawRoundedRect(0, 0, self.scaled_pixmap.width(), self.scaled_pixmap.height(), 10, 10)


    def update_size(self, new_size):
        super().update_size(new_size)
        self.update_image_size()



class CounterWidgetNumberOnly(CounterWidgetBase):
    def __init__(self, count, color=Qt.red, size=100, parent=None):
        super().__init__(color=color, size=size, parent=parent)
        self.count = count
        self.max_digits = 3  # Adjust as needed
        self.update_size(size)

    def compute_fixed_width(self):
        font_size = self.size
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            self.number_font = QFont(font_family[0], font_size, QFont.Bold)
        else:
            self.number_font = QFont("Arial", font_size, QFont.Bold)
        fm = QFontMetrics(self.number_font)
        max_number = '8' * self.max_digits
        self.fixed_width = fm.horizontalAdvance(max_number)
        self.fixed_height = fm.height()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.number_font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(str(self.count))
        text_height = fm.height()
        self.setFixedSize(self.fixed_width, self.fixed_height)
        text_x = (self.fixed_width - text_width) / 2
        text_y = self.fixed_height - fm.descent()
        painter.setPen(Qt.black)
        outline_thickness = 1
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(int(text_x + dx), int(text_y + dy), str(self.count))
        painter.setPen(Qt.white)
        painter.drawText(int(text_x), int(text_y), str(self.count))

    def update_size(self, new_size):
        super().update_size(new_size)
        self.compute_fixed_width()




class CounterWidgetImagesAndNumber(CounterWidgetBase):
    def __init__(self, count, image_path, color=Qt.red, size=100, show_frame=True, parent=None):
        super().__init__(color=color, size=size, parent=parent)
        self.count = count
        self.image_path = image_path
        self.show_frame = show_frame
        self.update_image_size()

    def update_image_size(self):
        pixmap = QPixmap(self.image_path)
        self.scaled_pixmap = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setFixedSize(self.scaled_pixmap.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.scaled_pixmap)
        font_size = int(self.size / 3)
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            number_font = QFont(font_family[0], font_size, QFont.Bold)
        else:
            number_font = QFont("Arial", font_size, QFont.Bold)
        painter.setFont(number_font)
        padding_x = max(5, int(self.size * 0.05))
        padding_y = max(5, int(self.size * 0.05))
        text_x = padding_x
        text_y = self.height() - padding_y
        painter.setPen(Qt.black)
        outline_thickness = 2
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(text_x + dx, text_y + dy, str(self.count))
        painter.setPen(Qt.white)
        painter.drawText(text_x, text_y, str(self.count))
        if self.show_frame:
            pen = QPen(self.color)
            pen.setWidth(int(self.size / 15))
            painter.setPen(pen)
            painter.drawRoundedRect(0, 0, self.scaled_pixmap.width(), self.scaled_pixmap.height(), 10, 10)



    def update_size(self, new_size):
        super().update_size(new_size)
        self.update_image_size()