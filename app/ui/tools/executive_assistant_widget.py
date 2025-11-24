from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                             QLabel, QComboBox, QHBoxLayout, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from app.ai.ai_manager import AIManager
from app.ui.icon_manager import IconManager

class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt, max_tokens):
        super().__init__()
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.ai_manager = AIManager.get_instance()

    def run(self):
        try:
            response = self.ai_manager.generate_text(self.prompt, self.max_tokens)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))

class ExecutiveAssistantWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = IconManager()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Asistente Ejecutivo")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #f0f0f0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)

        # Quick Actions
        actions_layout = QHBoxLayout()
        self.btn_summarize = QPushButton("Resumir")
        self.btn_summarize.setIcon(self.icon_manager.get_icon("file-alt", size=14))
        
        self.btn_improve = QPushButton("Mejorar Texto")
        self.btn_improve.setIcon(self.icon_manager.get_icon("magic", size=14))
        
        self.btn_extract = QPushButton("Extraer Tareas")
        self.btn_extract.setIcon(self.icon_manager.get_icon("tasks", size=14))
        
        for btn in [self.btn_summarize, self.btn_improve, self.btn_extract]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #f0f0f0;
                    border: 1px solid #666;
                    padding: 5px 10px;
                    border-radius: 4px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)
            actions_layout.addWidget(btn)
        
        self.layout.addLayout(actions_layout)

        # Input Area
        self.input_label = QLabel("Texto de entrada / Instrucción:")
        self.layout.addWidget(self.input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Pega aquí el texto a procesar o escribe tu instrucción...")
        self.input_text.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555; border-radius: 4px;")
        self.layout.addWidget(self.input_text)

        # Generate Button
        self.btn_generate = QPushButton("Procesar con IA")
        self.btn_generate.setIcon(self.icon_manager.get_icon("robot", size=16))
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_generate.clicked.connect(self.start_generation)
        self.layout.addWidget(self.btn_generate)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # Output Area
        self.output_label = QLabel("Respuesta:")
        self.layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #3a3a3a; color: #f0f0f0; border: 1px solid #555; border-radius: 4px;")
        self.layout.addWidget(self.output_text)

        # Connect Quick Actions
        self.btn_summarize.clicked.connect(lambda: self.set_preset_prompt("Resumir"))
        self.btn_improve.clicked.connect(lambda: self.set_preset_prompt("Mejorar"))
        self.btn_extract.clicked.connect(lambda: self.set_preset_prompt("Extraer"))

    def set_preset_prompt(self, action):
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Texto vacío", "Por favor, escribe o pega el texto que quieres procesar primero.")
            return

        if action == "Resumir":
            prompt = f"Resume el siguiente texto en puntos clave concisos:\n\n{text}"
        elif action == "Mejorar":
            prompt = f"Mejora la redacción del siguiente texto para que sea más profesional y claro:\n\n{text}"
        elif action == "Extraer":
            prompt = f"Extrae todas las tareas, fechas y acciones pendientes del siguiente texto y preséntalas como una lista de verificación:\n\n{text}"
        
        self.start_generation(prompt_override=prompt)

    def start_generation(self, prompt_override=None):
        prompt = prompt_override if prompt_override else self.input_text.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Entrada vacía", "Por favor escribe algo para procesar.")
            return

        self.btn_generate.setEnabled(False)
        self.progress_bar.show()
        self.output_text.clear()

        self.worker = AIWorker(prompt, max_tokens=2000)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, response):
        self.output_text.setPlainText(response)
        self.cleanup_worker()

    def on_generation_error(self, error_msg):
        self.output_text.setPlainText(f"Error: {error_msg}")
        self.cleanup_worker()

    def cleanup_worker(self):
        self.btn_generate.setEnabled(True)
        self.progress_bar.hide()
