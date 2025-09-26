import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime

from app.db import kanban_manager

class GanttChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagrama de Gantt")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.title_label = QLabel("Diagrama de Gantt")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.gantt_view = QWebEngineView()
        self.layout.addWidget(self.gantt_view)

        self.export_button = QPushButton("Exportar a HTML")
        self.export_button.clicked.connect(self.export_to_html)
        self.layout.addWidget(self.export_button)
        
        self.html_content = "" 

        self.load_gantt_chart()

    def get_assignee_initials(self, assignee_name):
        if not assignee_name or not isinstance(assignee_name, str):
            return ""
        names = assignee_name.split()
        initials = [name[0].upper() for name in names if name]
        return "".join(initials[:2])

    def transform_cards_to_frappe_data(self, cards):
        frappe_data = []
        for card in cards:
            start_date = card.get('started_at') or card.get('created_at')
            end_date = card.get('finished_at') or card.get('due_date')

            if not start_date or not end_date:
                continue

            try:
                start_str = datetime.fromisoformat(start_date.split('.')[0]).strftime('%Y-%m-%d')
                end_str = datetime.fromisoformat(end_date.split('.')[0]).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                continue

            progress = 0
            if card['column_name'] == "En Progreso":
                progress = 50 # Representing in-progress
            elif card['column_name'] == "Realizadas":
                progress = 100
            
            assignee_initials = self.get_assignee_initials(card.get('assignee'))
            task_name = f"{card['title']} ({assignee_initials})" if assignee_initials else card['title']

            frappe_data.append({
                "id": str(card['id']),
                "name": task_name,
                "start": start_str,
                "end": end_str,
                "progress": progress,
                "dependencies": ""
            })
        return frappe_data

    def load_gantt_chart(self):
        all_columns = kanban_manager.get_all_columns()
        all_cards = []
        for column in all_columns:
            cards_in_column = kanban_manager.get_cards_by_column(column['id'])
            for card_row in cards_in_column:
                card = dict(card_row)
                card['column_name'] = column['name']
                all_cards.append(card)
        
        if not all_cards:
            self.gantt_view.setHtml("<h1>No hay tarjetas Kanban para mostrar.</h1>")
            return

        gantt_data = self.transform_cards_to_frappe_data(all_cards)
        
        if not gantt_data:
            self.gantt_view.setHtml("<h1>No hay tareas con fechas válidas para generar el Gantt.</h1>")
            return

        tasks_json = json.dumps(gantt_data)

        # JavaScript to force header text to white
        js_force_white_header = """
                    const headerTexts = document.querySelectorAll('#gantt .grid-header text');
                    headerTexts.forEach(text => {
                        text.setAttribute("fill", "#ffffff");
                    });
        """

        self.html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Frappe Gantt</title>
            <script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.css" rel="stylesheet">
            <style>
                body {{
                    background-color: #2c2c2c;
                    color: #e0e0e0;
                    font-family: 'Segoe UI', Roboto, sans-serif;
                }}
                .gantt .grid-background {{
                    fill: #2c2c2c;
                }}
                .gantt .grid-header, .gantt .grid-row {{
                    fill: #555555;
                }}
                .gantt .upper-text, .gantt .lower-text {{
                    fill: #ffffff !important;
                }}
                .gantt .grid-row:nth-child(even) {{
                    fill: #333333;
                }}
                .gantt .row-line, .gantt .grid-header .row-line {{
                     stroke: #4a4a4a;
                }}
                .gantt .tick {{
                    stroke: #666666;
                }}
                .gantt .task-name {{
                    min-width: 350px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .gantt .task-name .bar-label, .gantt .task-name .bar-label.big {{
                    fill: #e8e8e8; 
                    font-weight: 500;
                }}
                .gantt .bar-wrapper:hover {{
                    opacity: 0.8;
                    cursor: pointer;
                }}
                .gantt .bar-progress {{
                    fill-opacity: 0.85;
                }}
                /* New Professional Color Palette */
                .gantt .bar[data-progress='100'] .bar-progress {{
                    fill: #4CAF50; /* Completed: A calm, positive green */
                }}
                .gantt .bar[data-progress='0'] .bar-progress {{
                    fill: #B0BEC5; /* To Do: A neutral, soft gray */
                }}
                .gantt .bar[data-progress='50'] .bar-progress {{
                    fill: #2196F3; /* In Progress: A clear, professional blue */
                }}
            </style>
        </head>
        <body>
            <svg id="gantt"></svg>
            <script>
                var tasks = {tasks_json};
                if (tasks.length > 0) {{
                    var gantt = new Gantt("#gantt", tasks, {{
                        header_height: 60,
                        column_width: 350,
                        step: 24,
                        view_modes: ['Day', 'Week', 'Month'],
                        bar_height: 24,
                        bar_corner_radius: 4,
                        padding: 20,
                        view_mode: 'Day',
                        language: 'es',
                        custom_popup_html: function(task) {{
                            return '<div class="details-container" style="padding:10px; background-color:#222; color: #fff; border-radius: 4px;">' +
                                '<h5>' + task.name + '</h5>' +
                                '<p>Inicio: ' + task._start.toLocaleDateString() + '</p>' +
                                '<p>Fin: ' + task._end.toLocaleDateString() + '</p>' +
                                '<p>Progreso: ' + task.progress + '%</p>' +
                            '</div>';
                        }}
                    }});

                }} else {{
                    document.getElementById('gantt').innerHTML = '<p style="text-align:center; margin-top: 50px;">No hay tareas para mostrar.</p>';
                }}
            </script>
        </body>
        </html>
        """
        self.gantt_view.setHtml(self.html_content)

    def export_to_html(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Gantt como HTML", "", "HTML Files (*.html)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.html_content)
            except Exception as e:
                print(f"Error saving HTML file: {e}")