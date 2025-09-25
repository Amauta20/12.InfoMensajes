from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PySide6.QtCore import Qt
from app.ui.productivity_widget import convert_utc_to_local, format_timestamp_to_local_display

class ViewKanbanCardDetailsDialog(QDialog):
    def __init__(self, card_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalles de la Tarjeta Kanban")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel(f"<b>Título:</b> {card_details['title']}")
        self.layout.addWidget(self.title_label)

        self.description_label = QLabel(f"<b>Descripción:</b> {card_details['description'] or 'N/A'}")
        self.layout.addWidget(self.description_label)

        self.created_at_label = QLabel(f"<b>Creada el:</b> {convert_utc_to_local(card_details['created_at'])}")
        self.layout.addWidget(self.created_at_label)

        self.started_at_label = QLabel(f"<b>Iniciada el:</b> {convert_utc_to_local(card_details['started_at'])}")
        self.layout.addWidget(self.started_at_label)

        self.finished_at_label = QLabel(f"<b>Finalizada el:</b> {convert_utc_to_local(card_details['finished_at'])}")
        self.layout.addWidget(self.finished_at_label)

        self.assignee_label = QLabel(f"<b>Encargado:</b> {card_details['assignee'] or 'N/A'}")
        self.layout.addWidget(self.assignee_label)

        self.due_date_label = QLabel(f"<b>Fecha de Entrega:</b> {format_timestamp_to_local_display(card_details['due_date']) or 'N/A'}")
        self.layout.addWidget(self.due_date_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        self.layout.addWidget(button_box)