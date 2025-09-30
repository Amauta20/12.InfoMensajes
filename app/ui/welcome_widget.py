from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QGroupBox, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtGui import QIcon
import datetime
from app.services import service_manager
from app.db import kanban_manager, checklist_manager, reminders_manager
from app.utils import time_utils

class WelcomeWidget(QWidget):
    add_service_requested = Signal(str, str, str) # name, url, icon
    show_kanban_requested = Signal()
    show_checklist_requested = Signal()
    show_reminders_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(20)

        self.welcome_label = QLabel("¡Bienvenido a InfoMensajero!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome_label)

        self.main_layout = QHBoxLayout()
        self.layout.addLayout(self.main_layout)

        # Tasks for the week
        self.tasks_group = QGroupBox("Tareas de la Semana")
        self.tasks_layout = QVBoxLayout(self.tasks_group)
        self.main_layout.addWidget(self.tasks_group)

        # Available services
        self.services_group = QGroupBox("Servicios Disponibles")
        self.services_layout = QGridLayout(self.services_group)
        self.main_layout.addWidget(self.services_group)

        self.load_tasks()
        self.load_available_services()

    def load_tasks(self):
        # Clear existing tasks
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tasks = self._get_tasks_for_week()
        if not tasks:
            self.tasks_layout.addWidget(QLabel("No hay tareas para esta semana."))
            return

        for task in tasks:
            task_label = QLabel(f"{task['type']}: {task['title']} (Vence: {task['due_date']})")
            self.tasks_layout.addWidget(task_label)

    def _get_tasks_for_week(self):
        start_of_week, end_of_week = time_utils.get_week_start_end()
        tasks = []

        # Kanban cards
        kanban_cards = kanban_manager.get_cards_due_between(start_of_week, end_of_week)
        for card in kanban_cards:
            tasks.append({
                "type": "Kanban",
                "title": card["title"],
                "due_date": card["due_date"],
            })

        # Checklist items
        checklist_items = checklist_manager.get_items_due_between(start_of_week, end_of_week)
        for item in checklist_items:
            tasks.append({
                "type": "Checklist",
                "title": item["text"],
                "due_date": item["due_at"],
            })

        # Reminders
        reminders = reminders_manager.get_reminders_due_between(start_of_week, end_of_week)
        for reminder in reminders:
            tasks.append({
                "type": "Recordatorio",
                "title": reminder["text"],
                "due_date": reminder["due_at"],
            })

        # Sort tasks by due date
        tasks.sort(key=lambda x: x["due_date"])

        return tasks

    def load_available_services(self):
        # Clear existing services
        while self.services_layout.count():
            child = self.services_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        catalog = service_manager.load_catalog()
        row, col = 0, 0
        for service in catalog:
            btn = QPushButton(QIcon(service.get("icon", "")), service["name"])
            btn.clicked.connect(lambda checked=False, name=service["name"], url=service["url"], icon=service.get("icon", ""): self.add_service_requested.emit(name, url, icon))
            self.services_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

    def refresh(self):
        self.load_tasks()