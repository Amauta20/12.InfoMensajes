from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QTextEdit, QMessageBox, QApplication)
from PyQt6.QtCore import Qt

class TemplatesWidget(QWidget):
    def __init__(self, templates_manager, parent=None):
        super().__init__(parent)
        self.templates_manager = templates_manager
        self.layout = QHBoxLayout(self)
        
        # Left: List
        left_layout = QVBoxLayout()
        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555;")
        self.templates_list.itemClicked.connect(self.load_template)
        left_layout.addWidget(QLabel("Plantillas Guardadas:"))
        left_layout.addWidget(self.templates_list)
        
        new_btn = QPushButton("Nueva Plantilla")
        new_btn.clicked.connect(self.clear_form)
        new_btn.setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 5px;")
        left_layout.addWidget(new_btn)
        
        self.layout.addLayout(left_layout, 1)
        
        # Right: Editor
        right_layout = QVBoxLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la plantilla")
        self.title_input.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555; padding: 5px;")
        right_layout.addWidget(QLabel("Título:"))
        right_layout.addWidget(self.title_input)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Contenido de la plantilla...")
        self.content_input.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555;")
        right_layout.addWidget(QLabel("Contenido:"))
        right_layout.addWidget(self.content_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_template)
        save_btn.setStyleSheet("background-color: #2980b9; color: white; border: none; padding: 5px 10px;")
        
        copy_btn = QPushButton("Copiar al Portapapeles")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        copy_btn.setStyleSheet("background-color: #8e44ad; color: white; border: none; padding: 5px 10px;")
        
        delete_btn = QPushButton("Eliminar")
        delete_btn.clicked.connect(self.delete_template)
        delete_btn.setStyleSheet("background-color: #c0392b; color: white; border: none; padding: 5px 10px;")
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(delete_btn)
        right_layout.addLayout(btn_layout)
        
        self.layout.addLayout(right_layout, 2)
        
        self.current_template_id = None
        self.refresh_list()

    def refresh_list(self):
        self.templates_list.clear()
        templates = self.templates_manager.get_all_templates()
        for tmpl in templates:
            item = QListWidgetItem(tmpl['title'])
            item.setData(Qt.ItemDataRole.UserRole, tmpl)
            self.templates_list.addItem(item)

    def load_template(self, item):
        tmpl = item.data(Qt.ItemDataRole.UserRole)
        self.current_template_id = tmpl['id']
        self.title_input.setText(tmpl['title'])
        self.content_input.setPlainText(tmpl['content'])

    def clear_form(self):
        self.current_template_id = None
        self.title_input.clear()
        self.content_input.clear()

    def save_template(self):
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        if not title or not content:
            QMessageBox.warning(self, "Error", "Título y contenido son obligatorios.")
            return

        if self.current_template_id:
            self.templates_manager.update_template(self.current_template_id, title, content, "General")
        else:
            self.templates_manager.add_template(title, content)
            
        self.refresh_list()
        self.clear_form()

    def delete_template(self):
        if not self.current_template_id: return
        
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta plantilla?") == QMessageBox.StandardButton.Yes:
            self.templates_manager.delete_template(self.current_template_id)
            self.refresh_list()
            self.clear_form()

    def copy_to_clipboard(self):
        content = self.content_input.toPlainText()
        if content:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            QMessageBox.information(self, "Copiado", "Contenido copiado al portapapeles.")
