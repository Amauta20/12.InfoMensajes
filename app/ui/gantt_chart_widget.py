from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timedelta
import json

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

        self.gantt_view = QWebEngineView()
        self.layout.addWidget(self.gantt_view)

        self.load_gantt_chart()

    def load_gantt_chart(self):
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
            return

        gantt_tasks = []
        for card in all_cards:
            start_date = None
            end_date = None
            progress = 0
            custom_class = ""

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
                    start_date = datetime.now() # Assume start now for planning
                    end_date = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
                    custom_class = "bar-todo"
                else:
                    start_date = datetime.now()
                    end_date = datetime.now() + timedelta(days=3) # Default 3 days for todo without due date
                    custom_class = "bar-todo"
            
            if start_date and end_date:
                gantt_tasks.append({
                    "id": str(card['id']),
                    "name": card['title'],
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "progress": progress,
                    "dependencies": "", # Not implemented yet
                    "custom_class": custom_class
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
