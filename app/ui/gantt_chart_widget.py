from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta
import json

from app.db import kanban_manager
from app.ui.utils import format_timestamp_to_local_display

class GanttChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QHBoxLayout(self) # Main layout for split view
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Left side: Task List
        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list_layout.setSpacing(5)

        self.task_list_label = QLabel("Tareas")
        self.task_list_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.task_list_layout.addWidget(self.task_list_label)

        self.task_list = QListWidget()
        self.task_list_layout.addWidget(self.task_list)

        self.main_layout.addWidget(self.task_list_widget, 1) # Stretch factor 1

        # Right side: Gantt Chart
        self.gantt_chart_container = QWidget()
        self.gantt_layout = QVBoxLayout(self.gantt_chart_container)
        self.gantt_layout.setContentsMargins(0, 0, 0, 0)
        self.gantt_layout.setSpacing(5)

        self.title_label = QLabel("Diagrama de Gantt")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.gantt_layout.addWidget(self.title_label)

        self.gantt_view = QWebEngineView()
        self.gantt_layout.addWidget(self.gantt_view)

        self.main_layout.addWidget(self.gantt_chart_container, 3) # Stretch factor 3

        self.load_gantt_chart()

    def load_gantt_chart(self):
        self.task_list.clear()
        all_columns = kanban_manager.get_all_columns()
        all_cards = []
        for column in all_columns:
            cards_in_column = kanban_manager.get_cards_by_column(column['id'])
            for card_row in cards_in_column:
                card = dict(card_row) # Convert Row to dictionary
                card['column_name'] = column['name']
                all_cards.append(card)
        
        if not all_cards:
            self.gantt_view.setHtml("<h1>No hay tarjetas Kanban para mostrar en el diagrama de Gantt.</h1>")
            self.task_list.addItem("No hay tareas.")
            return

        # Sort cards by due date or created date
        all_cards.sort(key=lambda x: x['due_date'] or x['created_at'])

        gantt_tasks = []
        for card in all_cards:
            # Populate task list
            assignee_name = card['assignee'] if card['assignee'] else "Sin asignar"
            task_list_item_text = f"{card['title']} ({assignee_name})"
            self.task_list.addItem(task_list_item_text)

            start_date = None
            end_date = None
            progress = 0
            custom_class = ""
            task_type = "task"

            task_name = card['title']
            if card['assignee']:
                task_name = f"{card['assignee']} - {task_name}"

            if card['column_name'] == "Realizadas":
                if card['started_at'] and card['finished_at']:
                    start_date = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['finished_at'] else datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S')
                    progress = 100
                    custom_class = "bar-milestone"
            elif card['column_name'] == "En Progreso":
                if card['started_at']:
                    start_date = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.now() + timedelta(days=7) # Assume 1 week more for in progress tasks
                    progress = 50 # Arbitrary progress for in-progress tasks
                    custom_class = "bar-progress"
            elif card['column_name'] == "Por Hacer":
                if card['due_date']:
                    start_date = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
                    end_date = start_date # Milestone
                    custom_class = "bar-todo"
                    task_type = "milestone"
                else:
                    start_date = datetime.now()
                    end_date = datetime.now() + timedelta(days=3) # Default 3 days for todo without due date
                    custom_class = "bar-todo"
                    task_type = "task"
            
            if start_date and end_date:
                gantt_tasks.append({
                    "id": str(card['id']),
                    "name": task_name,
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "progress": progress,
                    "dependencies": "", # Not implemented yet
                    "custom_class": custom_class,
                    "type": task_type
                })

        # HTML template for the Gantt chart
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gantt Chart</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.0/dist/frappe-gantt.css">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; margin: 0; padding: 0; background-color: #2b2b2b; color: #f0f0f0; }}
                .gantt-container {{ background-color: #2b2b2b; }}
                .gantt .bar-milestone {{ fill: #28a745; }} /* Green for completed */
                .gantt .bar-progress {{ fill: #007bff; }} /* Blue for in progress */
                .gantt .bar-todo {{ fill: #ffc107; }} /* Yellow for todo */
                .gantt .bar-label {{ fill: #f0f0f0; }}
                .gantt .grid-header {{ fill: #FFFFFF; stroke: #555555; }}
                .gantt .grid-row {{ fill: #2b2b2b; stroke: #555555; }}
                .gantt .tick {{ stroke: #555555; }}
                .gantt .today-highlight {{ fill: #555555; opacity: 0.5; }}
            </style>
        </head>
        <body>
            <div id="gantt-chart"></div>

            <script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.0/dist/frappe-gantt.min.js"></script>
            <script>
                var tasks = {json.dumps(gantt_tasks)};

                var gantt = new Gantt("#gantt-chart", tasks, {{
                    on_click: function (task) {{
                        console.log(task);
                    }},
                    on_date_change: function (task, start, end) {{
                        console.log(task, start, end);
                    }},
                    on_progress_change: function (task, progress) {{
                        console.log(task, progress);
                    }},
                    on_view_change: function (mode) {{
                        console.log(mode);
                    }},
                    view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'],
                    language: 'es' // Set language to Spanish
                }});
                gantt.change_view_mode('Week');
            </script>
        </body>
        </html>
        """
        self.gantt_view.setHtml(html_content)
