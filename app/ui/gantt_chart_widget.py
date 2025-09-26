from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
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

    def get_assignee_initials(self, assignee_name):
        if not assignee_name: return ""
        names = assignee_name.split()
        initials = [name[0].upper() for name in names if name]
        return "".join(initials[:2]) # Take up to two initials

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

        # Sort cards by due date or created date
        all_cards.sort(key=lambda x: x['due_date'] or x['created_at'])

        # Determine overall date range for the chart
        min_chart_date = datetime.max
        max_chart_date = datetime.min

        for card in all_cards:
            start_dt = None
            end_dt = None

            if card['column_name'] == "Realizadas" and card['started_at'] and card['finished_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['finished_at'] else datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S')
            elif card['column_name'] == "En Progreso" and card['started_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.now() + timedelta(days=7) # Assume 1 week more for in progress tasks
            elif card['column_name'] == "Por Hacer" and card['due_date']:
                start_dt = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
                end_dt = start_dt # Milestone
            elif card['created_at']:
                start_dt = datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['created_at'] else datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = start_dt + timedelta(days=1) # Default small duration
            
            if start_dt and start_dt < min_chart_date: min_chart_date = start_dt
            if end_dt and end_dt > max_chart_date: max_chart_date = end_dt

        if min_chart_date == datetime.max or max_chart_date == datetime.min:
            self.gantt_view.setHtml("<h1>No se pudieron determinar las fechas para el diagrama de Gantt.</h1>")
            return

        # Extend date range for better visualization
        min_chart_date = min_chart_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        max_chart_date = max_chart_date.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=7)

        total_days = (max_chart_date - min_chart_date).days + 1
        if total_days <= 0: total_days = 1 # Avoid division by zero

        # Generate HTML content
        html_rows = []
        html_rows.append("<div class=\"gantt-header-row\">")
        html_rows.append("<div class=\"task-details-header\">Tarea / Encargado</div>")
        html_rows.append("<div class=\"gantt-timeline-header\">")
        
        current_date = min_chart_date
        while current_date <= max_chart_date:
            html_rows.append(f"<div class=\"timeline-day\">{current_date.day}/{current_date.month}</div>")
            current_date += timedelta(days=1)
        html_rows.append("</div>")
        html_rows.append("</div>")

        for i, card in enumerate(all_cards):
            row_class = "gantt-row-even" if i % 2 == 0 else "gantt-row-odd"
            html_rows.append(f"<div class=\"gantt-row {row_class}\">")

            assignee_initials = self.get_assignee_initials(card['assignee'])
            task_details_html = f"<div class=\"task-title\">{card['title']}</div>"
            if assignee_initials:
                task_details_html += f"<div class=\"assignee-initials\">({assignee_initials})</div>"
            html_rows.append(f"<div class=\"task-details\">{task_details_html}</div>")

            # Gantt bar calculation
            start_dt = None
            end_dt = None
            bar_color = "#6c757d" # Default grey

            if card['column_name'] == "Realizadas" and card['started_at'] and card['finished_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['finished_at'] else datetime.strptime(card['finished_at'], '%Y-%m-%d %H:%M:%S')
                bar_color = "#28a745" # Green for completed
            elif card['column_name'] == "En Progreso" and card['started_at']:
                start_dt = datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['started_at'] else datetime.strptime(card['started_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.now() + timedelta(days=7) # Assume 1 week more for in progress tasks
                bar_color = "#007bff" # Blue for in progress
            elif card['column_name'] == "Por Hacer" and card['due_date']:
                start_dt = datetime.strptime(card['due_date'], '%Y-%m-%d %H:%M:%S')
                end_dt = start_dt # Milestone
                bar_color = "#ffc107" # Yellow for todo
            elif card['created_at']:
                start_dt = datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in card['created_at'] else datetime.strptime(card['created_at'], '%Y-%m-%d %H:%M:%S')
                end_dt = start_dt + timedelta(days=1) # Default small duration
                bar_color = "#6c757d" # Default grey

            gantt_bar_html = "<div class=\"gantt-bar-container\">";
            if start_dt and end_dt:
                # Calculate position and width of the bar
                start_offset_days = (start_dt - min_chart_date).days
                end_offset_days = (end_dt - min_chart_date).days
                duration_days = (end_dt - start_dt).days + 1

                # Ensure duration is at least 1 day for visibility
                if duration_days <= 0: duration_days = 1

                # Calculate percentage for left offset and width
                # Total timeline width is 100%
                left_percent = (start_offset_days / total_days) * 100
                width_percent = (duration_days / total_days) * 100

                # For milestones, make it a small dot or diamond
                if card['column_name'] == "Por Hacer" and card['due_date']:
                    gantt_bar_html += f"<div class=\"gantt-milestone\" style=\"left: {{left_percent}}%; background-color: {{bar_color}};\"></div>"
                else:
                    gantt_bar_html += f"<div class=\"gantt-bar\" style=\"left: {{left_percent}}%; width: {{width_percent}}%; background-color: {{bar_color}};\"></div>"
            gantt_bar_html += "</div>"
            html_rows.append(f"<div class=\"gantt-chart-area\">{gantt_bar_html}</div>")
            html_rows.append("</div>") # Close gantt-row

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Diagrama de Gantt</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #2b2b2b; color: #f0f0f0; }}
                .gantt-container {{ display: flex; flex-direction: column; width: 100%; }}
                .gantt-header-row, .gantt-row {{ display: flex; border-bottom: 1px solid #444; }}
                .gantt-header-row {{ background-color: #3a3a3a; font-weight: bold; }}
                .task-details-header, .task-details {{ flex: 0 0 200px; padding: 8px; border-right: 1px solid #444; }}
                .gantt-timeline-header, .gantt-chart-area {{ flex-grow: 1; display: flex; position: relative; }}
                .timeline-day {{ flex-grow: 1; text-align: center; padding: 8px 0; border-right: 1px solid #444; font-size: 0.8em; color: #FFFFFF; }}
                .timeline-day:last-child {{ border-right: none; }}

                .gantt-row-even {{ background-color: #2e2e2e; }}
                .gantt-row-odd {{ background-color: #363636; }}

                .task-title {{ font-weight: bold; color: #f0f0f0; }}
                .assignee-initials {{ font-size: 0.8em; color: #cccccc; }}

                .gantt-bar-container {{ position: relative; width: 100%; height: 100%; }}
                .gantt-bar, .gantt-milestone {{ position: absolute; height: 70%; top: 15%; border-radius: 3px; opacity: 0.8; }}
                .gantt-bar {{ height: 70%; top: 15%; }}
                .gantt-milestone {{ width: 10px; height: 10px; border-radius: 50%; transform: translateX(-50%); }} /* Circle for milestone */

                /* Colors for bars */
                .bar-milestone {{ background-color: #28a745; }} /* Green for completed */
                .bar-progress {{ background-color: #007bff; }} /* Blue for in progress */
                .bar-todo {{ background-color: #ffc107; }} /* Yellow for todo */
            </style>
        </head>
        <body>
            <div class="gantt-container">
                {''.join(html_rows)}
            </div>
        </body>
        </html>
        """
        self.gantt_view.setHtml(html_content)
