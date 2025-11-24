from PyQt6.QtWidgets import QTextEdit, QPushButton, QMessageBox
from app.ui.base_dialog import BaseDialog
from app.ai.ai_manager import AIManager

class EditNoteDialog(BaseDialog):
    def __init__(self, initial_content="", parent=None):
        super().__init__("Editar Nota", parent)
        self.setFixedSize(400, 300)

        self.note_editor = QTextEdit()
        self.note_editor.setPlainText(initial_content)
        self.add_content(self.note_editor)
        self.note_editor.setFocus()

        # Add AI Assistant button
        self.ai_button = QPushButton("Asistente IA")
        self.ai_button.clicked.connect(self.run_ai_assistant)
        self.button_box.addButton(self.ai_button, self.button_box.ButtonRole.ActionRole)

    def get_new_content(self):
        return self.note_editor.toPlainText().strip()

    def run_ai_assistant(self):
        """
        Runs the AI assistant to improve the text in the note editor.
        """
        current_text = self.note_editor.toPlainText().strip()
        if not current_text:
            QMessageBox.information(self, "Asistente IA", "No hay texto para mejorar.")
            return

        try:
            ai_manager = AIManager.get_instance()
            prompt = f"Revisa y mejora la redacción, ortografía y gramática del siguiente texto. Devuelve solo el texto mejorado, sin añadir introducciones ni despedidas:\n\n{current_text}"
            
            # Show a busy message
            self.ai_button.setText("Procesando...")
            self.ai_button.setEnabled(False)
            self.repaint() # Force repaint to show the disabled state

            improved_text = ai_manager.generate_text(prompt)
            
            self.note_editor.setPlainText(improved_text)

        except PermissionError as e:
            QMessageBox.warning(self, "Asistente IA no disponible", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error del Asistente IA", f"Ocurrió un error inesperado: {e}")
        finally:
            # Restore button state
            self.ai_button.setText("Asistente IA")
            self.ai_button.setEnabled(True)
