from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QComboBox, 
                             QLineEdit, QDialog, QFormLayout, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt

class RuleDialog(QDialog):
    def __init__(self, parent=None, rule=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Regla" if rule else "Nueva Regla")
        self.setMinimumWidth(400)
        self.rule = rule
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        if rule: self.name_input.setText(rule['name'])
        form_layout.addRow("Nombre:", self.name_input)
        
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["pomodoro_finished", "app_start", "pomodoro_break_finished"])
        if rule: self.trigger_combo.setCurrentText(rule['trigger_type'])
        form_layout.addRow("Disparador:", self.trigger_combo)
        
        self.action_combo = QComboBox()
        self.action_combo.addItems(["show_notification", "play_sound", "open_url"])
        if rule: self.action_combo.setCurrentText(rule['action_type'])
        form_layout.addRow("Acción:", self.action_combo)
        
        self.params_input = QTextEdit()
        self.params_input.setPlaceholderText('{"message": "Hola"} o {"url": "https://..."}')
        if rule: self.params_input.setText(rule['action_params'])
        form_layout.addRow("Parámetros (JSON):", self.params_input)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        import json
        try:
            params = json.loads(self.params_input.toPlainText())
        except:
            params = {}
            
        return {
            "name": self.name_input.text(),
            "trigger_type": self.trigger_combo.currentText(),
            "action_type": self.action_combo.currentText(),
            "action_params": params
        }

class RulesEditor(QWidget):
    def __init__(self, rules_manager, parent=None):
        super().__init__(parent)
        self.rules_manager = rules_manager
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Motor de Reglas Inteligentes")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #f0f0f0;")
        header_layout.addWidget(title)
        
        add_btn = QPushButton("Nueva Regla")
        add_btn.clicked.connect(self.add_rule)
        add_btn.setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 5px 10px; border-radius: 3px;")
        header_layout.addWidget(add_btn)
        
        self.layout.addLayout(header_layout)
        
        # List
        self.rules_list = QListWidget()
        self.rules_list.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555;")
        self.layout.addWidget(self.rules_list)
        
        # Actions
        actions_layout = QHBoxLayout()
        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(self.edit_rule)
        delete_btn = QPushButton("Eliminar")
        delete_btn.clicked.connect(self.delete_rule)
        
        for btn in [edit_btn, delete_btn]:
            btn.setStyleSheet("background-color: #555; color: white; border: none; padding: 5px 10px; border-radius: 3px;")
            actions_layout.addWidget(btn)
            
        self.layout.addLayout(actions_layout)
        
        self.refresh_list()

    def refresh_list(self):
        self.rules_list.clear()
        rules = self.rules_manager.get_all_rules()
        for rule in rules:
            item = QListWidgetItem(f"{rule['name']} ({rule['trigger_type']} -> {rule['action_type']})")
            item.setData(Qt.ItemDataRole.UserRole, rule)
            self.rules_list.addItem(item)

    def add_rule(self):
        dialog = RuleDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.rules_manager.add_rule(data['name'], data['trigger_type'], data['action_type'], data['action_params'])
            self.refresh_list()

    def edit_rule(self):
        current_item = self.rules_list.currentItem()
        if not current_item: return
        
        rule = current_item.data(Qt.ItemDataRole.UserRole)
        dialog = RuleDialog(self, rule)
        if dialog.exec():
            data = dialog.get_data()
            self.rules_manager.update_rule(rule['id'], data['name'], data['trigger_type'], data['action_type'], data['action_params'], rule['is_active'])
            self.refresh_list()

    def delete_rule(self):
        current_item = self.rules_list.currentItem()
        if not current_item: return
        
        rule = current_item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta regla?") == QMessageBox.StandardButton.Yes:
            self.rules_manager.delete_rule(rule['id'])
            self.refresh_list()
