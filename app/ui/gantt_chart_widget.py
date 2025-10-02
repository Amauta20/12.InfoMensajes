from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import json
import os
from app.db import settings_manager

class GanttChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.dependencies = []
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.export_button = QPushButton("Export to HTML")
        self.export_button.clicked.connect(self.export_to_html)
        self.layout.addWidget(self.export_button)

        self.setLayout(self.layout)



    def load_gantt_chart(self, tasks, dependencies):
        print("--- Entering load_gantt_chart ---")
        try:
            self.tasks = tasks
            self.dependencies = dependencies
            print("Generating Gantt HTML...")
            html_content = self._generate_gantt_html()
            print("Setting HTML content...")
            self.web_view.setHtml(html_content)
            print("HTML content set.")
        except Exception as e:
            print(f"--- ERROR in load_gantt_chart: {e} ---")
        print("--- Exiting load_gantt_chart ---")

    def _generate_gantt_html(self):
        print("--- Entering _generate_gantt_html ---")
        try:
            tasks_json = json.dumps(self.tasks)
            dependencies_json = json.dumps(self.dependencies)

            # Get colors from settings
            todo_color = settings_manager.get_todo_color()
            inprogress_color = settings_manager.get_inprogress_color()
            done_color = settings_manager.get_done_color()

            html_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gantt Chart</title>
                <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                <script type="text/javascript">
                    google.charts.load('current', {{'packages':['gantt']}});
                    google.charts.setOnLoadCallback(drawChart);

                    function drawChart() {{
                        try {{
                            const data = new google.visualization.DataTable();
                            data.addColumn('string', 'Task ID');
                            data.addColumn('string', 'Task Name');
                            data.addColumn('string', 'Resource');
                            data.addColumn('date', 'Start Date');
                            data.addColumn('date', 'End Date');
                            data.addColumn('number', 'Duration');
                            data.addColumn('number', 'Percent Complete');
                            data.addColumn('string', 'Dependencies');

                            const tasks = {tasks_json};
                            const dependencies = {dependencies_json};

                            const colorMap = {{
                                "not_started": "{todo_color}",
                                "in_progress": "{inprogress_color}",
                                "completed": "{done_color}"
                            }};

                            tasks.forEach((task, index) => {{
                                const startDate = new Date(task.start);
                                const endDate = new Date(task.end);
                                let duration = endDate.getTime() - startDate.getTime();

                                if (duration === 0 && task.status === "not_started") {{
                                    duration = 24 * 60 * 60 * 1000;
                                }} else if (duration === 0) {{
                                    duration = 24 * 60 * 60 * 1000;
                                }}

                                data.addRow([
                                    'Task' + index,
                                    task.name,
                                    task.status,
                                    startDate,
                                    endDate,
                                    duration,
                                    100,
                                    null
                                ]);
                            }});

                            const options = {{
                                gantt: {{
                                    trackHeight: 30,
                                    dayOfWeekEnabled: false,
                                    labelStyle: {{
                                        fontName: 'Arial',
                                        fontSize: 10
                                    }},
                                    criticalPathEnabled: false,
                                    arrow: {{
                                        angle: 100,
                                        width: 5,
                                        color: '#555',
                                        radius: 0
                                    }},
                                    palette: [
                                        {{
                                            "color": colorMap["not_started"],
                                            "dark": colorMap["not_started"],
                                            "light": colorMap["not_started"]
                                        }},
                                        {{
                                            "color": colorMap["in_progress"],
                                            "dark": colorMap["in_progress"],
                                            "light": colorMap["in_progress"]
                                        }},
                                        {{
                                            "color": colorMap["completed"],
                                            "dark": colorMap["completed"],
                                            "light": colorMap["completed"]
                                        }}
                                    ]
                                }}
                            }};

                            const chart = new google.visualization.Gantt(document.getElementById('chart_div'));
                            chart.draw(data, options);
                        }} catch (e) {{
                            console.error("Error drawing Gantt chart:", e);
                        }}
                    }}
                </script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; overflow: hidden; }}
                    #chart_div {{ width: 100%; height: 100vh; }}
                </style>
            </head>
            <body>
                <div id="chart_div"></div>
            </body>
            </html>
            '''

            html_content = html_template.format(
                tasks_json=tasks_json,
                dependencies_json=dependencies_json,
                todo_color=todo_color,
                inprogress_color=inprogress_color,
                done_color=done_color
            )
            print("--- Exiting _generate_gantt_html ---")
            return html_content
        except Exception as e:
            print(f"--- ERROR in _generate_gantt_html: {e} ---")
            return ""

    def export_to_html(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Gantt Chart to HTML", "", "HTML Files (*.html);;All Files (*)")
        if file_path:
            self.web_view.page().toHtml(lambda html_content: self._save_html_to_file(file_path, html_content))

    def _save_html_to_file(self, file_path, html_content):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Gantt chart exported to {file_path}")
        except Exception as e:
            print(f"Error exporting Gantt chart: {e}")
