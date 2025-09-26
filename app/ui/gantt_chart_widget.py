from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

from app.db import kanban_manager
from app.ui.utils import format_timestamp_to_local_display

class GanttChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.title_label = QLabel("Diagrama de Gantt")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.gantt_output = QTextEdit()
        self.gantt_output.setReadOnly(True)
        self.gantt_output.setFontFamily("monospace")
        self.layout.addWidget(self.gantt_output)

        self.load_gantt_chart()

    def load_gantt_chart(self):
        self.gantt_output.clear()
        all_columns = kanban_manager.get_all_columns()
        all_cards = []
        for column in all_columns:
            cards_in_column = kanban_manager.get_cards_by_column(column['id'])
            for card_row in cards_in_column:
                card = dict(card_row) # Convert Row to dictionary
                card['column_name'] = column['name']
                all_cards.append(card)
        
        if not all_cards:
            self.gantt_output.setText("No hay tarjetas Kanban para mostrar en el diagrama de Gantt.")
            return

        # Sort cards by due date or created date
        all_cards.sort(key=lambda x: x['due_date'] or x['created_at'])

        # Determine date range
        min_date = datetime.max
        max_date = datetime.min

        for card in all_cards:
            if card['created_at']:
                created_dt = datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['created_at'] else datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S')
                if created_dt < min_date: min_date = created_dt
            if card['due_date']:
                due_dt = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
                if due_dt > max_date: max_date = due_dt
            if card['finished_at']:
                finished_dt = datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['finished_at'] else datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S')
                if finished_dt > max_date: max_date = finished_dt
            if card['started_at']:
                started_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                if started_dt < min_date: min_date = started_dt

        if min_date == datetime.max or max_date == datetime.min:
            self.gantt_output.setText("No se pudieron determinar las fechas para el diagrama de Gantt.")
            return

        # Extend date range for better visualization
        min_date = min_date - timedelta(days=7)
        max_date = max_date + timedelta(days=7)

        # Generate timeline header
        timeline_header = " " * 30 # Space for task title
        current_date = min_date
        while current_date <= max_date:
            timeline_header += current_date.strftime("%m/%d ")
            current_date += timedelta(days=1)
        self.gantt_output.append(timeline_header)
        self.gantt_output.append("-" * len(timeline_header))

        # Generate task bars
        for card in all_cards:
            task_line = f"{card['title'][:25]:<25} "
            
            start_dt = None
            end_dt = None

            if card['column_name'] == "Realizadas" and card['started_at'] and card['finished_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['finished_at'] else datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S')
            elif card['column_name'] == "En Progreso" and card['started_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.now() # Currently in progress
            elif card['column_name'] == "Por Hacer" and card['due_date']:
                start_dt = datetime.now() # Assume start now for planning
                end_dt = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
            elif card['created_at']:
                start_dt = datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['created_at'] else datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = start_dt + timedelta(days=1) # Default small duration

            if start_dt and end_dt:
                current_day = min_date
                while current_day <= max_date:
                    if start_dt.date() <= current_day.date() <= end_dt.date():
                        task_line += "X " # Represent task duration
                    else:
                        task_line += "  " # Empty space
                    current_day += timedelta(days=1)
            else:
                task_line += "No dates available"

            self.gantt_output.append(task_line)
