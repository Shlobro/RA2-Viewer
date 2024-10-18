from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QCheckBox, QLabel, QSpinBox, QHBoxLayout
from PySide6.QtGui import QPixmap
from common import (name_to_path)

class SelectUnitWidget(QWidget):
    selection_changed = Signal(str, str, str, bool)  # Faction, unit_type, unit_name, is_selected

    def __init__(self, faction, unit_type, unit_name, selected_units, parent=None):
        super().__init__(parent)
        self.faction = faction
        self.unit_type = unit_type
        self.unit_name = unit_name
        self.selected_units = selected_units  # Reference to the selected_units_dict['selected_units']

        # Create controls
        self.select_checkbox = QCheckBox()
        self.lock_checkbox = QCheckBox("Lock")
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(1, 100)  # Adjust the range as needed

        # Initially, lock_checkbox and priority_spinbox are disabled
        self.lock_checkbox.setEnabled(False)
        self.priority_spinbox.setEnabled(False)

        # Create labels
        self.name_label = QLabel(self.unit_name)
        image_path = name_to_path(self.unit_name)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_label = QLabel()
            self.image_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
        else:
            self.image_label = QLabel("No Image")

        # Arrange controls in layout
        layout = QHBoxLayout()
        layout.addWidget(self.select_checkbox)
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.lock_checkbox)
        layout.addWidget(QLabel("Priority:"))
        layout.addWidget(self.priority_spinbox)
        layout.addStretch()
        self.setLayout(layout)

        # Connect signals
        self.select_checkbox.stateChanged.connect(self.on_select_changed)

        # Initialize states from selected_units
        is_selected = self.is_unit_selected()
        self.select_checkbox.setChecked(is_selected)
        self.lock_checkbox.setEnabled(is_selected)
        self.priority_spinbox.setEnabled(is_selected)
        if is_selected:
            is_locked = self.get_unit_lock_state()
            priority = self.get_unit_priority()
            self.lock_checkbox.setChecked(is_locked)
            self.priority_spinbox.setValue(priority)

        # Connect other signals
        self.lock_checkbox.stateChanged.connect(self.on_lock_changed)
        self.priority_spinbox.valueChanged.connect(self.on_priority_changed)

    def is_unit_selected(self):
        return self.selected_units.get(self.faction, {}).get(self.unit_type, {}).get(self.unit_name, {}).get('selected',
                                                                                                             False)

    def get_unit_lock_state(self):
        return self.selected_units.get(self.faction, {}).get(self.unit_type, {}).get(self.unit_name, {}).get('locked',
                                                                                                             False)

    def get_unit_priority(self):
        return self.selected_units.get(self.faction, {}).get(self.unit_type, {}).get(self.unit_name, {}).get('priority',
                                                                                                             1)

    def on_select_changed(self, state):
        is_selected = (state == Qt.Checked)
        # Enable or disable lock checkbox and priority spinbox
        self.lock_checkbox.setEnabled(is_selected)
        self.priority_spinbox.setEnabled(is_selected)
        # Update selected_units
        if is_selected:
            # Ensure the hierarchy exists
            self.selected_units.setdefault(self.faction, {}).setdefault(self.unit_type, {}).setdefault(self.unit_name,
                                                                                                       {})
            self.selected_units[self.faction][self.unit_type][self.unit_name]['selected'] = True
            # Also save the current lock state and priority
            self.selected_units[self.faction][self.unit_type][self.unit_name]['locked'] = self.lock_checkbox.isChecked()
            self.selected_units[self.faction][self.unit_type][self.unit_name][
                'priority'] = self.priority_spinbox.value()
        else:
            # Remove unit from selected_units
            if self.faction in self.selected_units and self.unit_type in self.selected_units[
                self.faction] and self.unit_name in self.selected_units[self.faction][self.unit_type]:
                del self.selected_units[self.faction][self.unit_type][self.unit_name]
                # Clean up empty dictionaries
                if not self.selected_units[self.faction][self.unit_type]:
                    del self.selected_units[self.faction][self.unit_type]
                if not self.selected_units[self.faction]:
                    del self.selected_units[self.faction]
        # Emit signal
        self.selection_changed.emit(self.faction, self.unit_type, self.unit_name, is_selected)

    def on_lock_changed(self, state):
        is_locked = (state == Qt.Checked)
        # Update selected_units
        if self.is_unit_selected():
            self.selected_units[self.faction][self.unit_type][self.unit_name]['locked'] = is_locked

    def on_priority_changed(self, value):
        # Update selected_units
        if self.is_unit_selected():
            self.selected_units[self.faction][self.unit_type][self.unit_name]['priority'] = value
