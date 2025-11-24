import json
import datetime
import logging
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel

from app.db.kanban_manager import KanbanManager
from app.db import settings_manager, database

class GanttBridge(QObject):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
    """
    Bridge object to allow communication from JavaScript (in QWebEngineView)
    to Python.
    """
    @pyqtSlot(int, str, str)
    def update_task_dates(self, task_id, start_date, end_date):
        """
        Slot that receives updated task data from the Gantt chart JS.
        """
        logging.debug(f"Received update from JS: ID={task_id}, Start={start_date}, End={end_date}")
        
        # The dates from dhtmlxGantt are in "YYYY-MM-DD HH:MM" format.
        # We need to parse them into datetime objects.
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M")

            # Fetch existing card details to preserve other fields
            card = self.manager.get_card_details(task_id)
            if card:
                self.manager.update_card(
                    card_id=task_id,
                    new_title=card['title'],
                    new_description=card['description'],
                    new_assignee=card['assignee'],
                    new_due_date=card['due_date'],
                    new_start_date=start_date_obj,
                    new_end_date=end_date_obj
                )
                logging.info(f"Successfully updated card {task_id} in the database.")
            else:
                logging.error(f"Error: Card with ID {task_id} not found.")

        except Exception as e:
            logging.error(f"Error updating card from Gantt: {e}", exc_info=True)


class GanttChartWidget(QWidget):
    def __init__(self, conn, settings_manager, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.kanban_manager = KanbanManager(self.conn)
        self.settings_manager = settings_manager
        self.tasks = []
        self.init_ui()
        self.refresh_gantt()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # --- Web View for Gantt ---
        self.web_view = QWebEngineView()
        self.page = QWebEnginePage(self)
        self.web_view.setPage(self.page)
        
        # --- Setup Bridge for JS -> Python communication ---
        self.bridge = GanttBridge(self.kanban_manager)
        self.channel = QWebChannel()
        self.channel.registerObject("ganttBridge", self.bridge)
        self.page.setWebChannel(self.channel)

        self.layout.addWidget(self.web_view)

        # --- Buttons ---
        self.export_html_button = QPushButton("Export to HTML")
        self.export_html_button.clicked.connect(self.export_to_html)
        self.layout.addWidget(self.export_html_button)

        self.export_png_button = QPushButton("Export to PNG")
        self.export_png_button.clicked.connect(self.export_to_png)
        self.layout.addWidget(self.export_png_button)

        self.setLayout(self.layout)

    def refresh_gantt(self):
        """
        Fetches all cards from the database and reloads the Gantt chart.
        """
        logging.info("Refreshing Gantt Chart")
        try:
            all_cards = self.kanban_manager.get_all_cards()
            self.tasks = self._transform_cards_to_gantt_tasks(all_cards)
            html_content = self._generate_gantt_html()
            self.web_view.setHtml(html_content)
            logging.info("Gantt chart reloaded successfully.")
        except Exception as e:
            logging.error(f"Error in refresh_gantt: {e}", exc_info=True)

    def _transform_cards_to_gantt_tasks(self, cards):
        gantt_tasks = []
        
        columns = self.kanban_manager.get_all_columns()
        column_map = {col['id']: col['name'] for col in columns}
        today = datetime.datetime.now()

        for card in cards:
            status = "not_started"
            column_name = column_map.get(card['column_id'])
            if column_name == "En Progreso":
                status = "in_progress"
            elif column_name == "Realizadas":
                status = "completed"

            task_details = {
                "id": card['id'],
                "name": card['title'],
                "status": status,
                "due_date": card['due_date'] if 'due_date' in card else None
            }

            # A task is a milestone if it is not started AND has no start date.
            is_milestone = (
                status == 'not_started' and
                ('start_date' not in card or not card['start_date']) and
                'due_date' in card and card['due_date']
            )

            if is_milestone:
                due_date = datetime.datetime.fromisoformat(card['due_date'])
                task_details["start"] = due_date.isoformat()
                task_details["type"] = "milestone"
            else:
                # All other tasks are bars, including those with a future start date.
                if 'start_date' in card and card['start_date'] and 'end_date' in card and card['end_date']:
                    start = datetime.datetime.fromisoformat(card['start_date'])
                    end = datetime.datetime.fromisoformat(card['end_date'])
                else:
                    # Fallback for tasks without start/end dates (e.g., legacy tasks)
                    start = datetime.datetime.fromisoformat(card['created_at'])
                    end = start + datetime.timedelta(days=1)
                
                task_details["start"] = start.isoformat()
                task_details["end"] = end.isoformat()

                if status == 'completed':
                    task_details["progress"] = 1.0
                elif status == 'in_progress' and 'due_date' in card and card['due_date'] and 'start_date' in card and card['start_date']:
                    start_date = datetime.datetime.fromisoformat(card['start_date'])
                    due_date = datetime.datetime.fromisoformat(card['due_date'])
                    
                    total_duration = (due_date - start_date).total_seconds()
                    elapsed_duration = (today - start_date).total_seconds()

                    if total_duration > 0:
                        progress = max(0, min(1, elapsed_duration / total_duration))
                        task_details["progress"] = round(progress, 2)
                    else:
                        task_details["progress"] = 0

            gantt_tasks.append(task_details)
        return gantt_tasks

    def _get_dhtmlx_color(self, status):
        if status == "not_started":
            return self.settings_manager.get_todo_color()
        elif status == "in_progress":
            return self.settings_manager.get_inprogress_color()
        elif status == "completed":
            return self.settings_manager.get_done_color()
        return "#808080" # Default grey

    def _generate_gantt_html(self):
        logging.debug("Generating Gantt HTML")
        
        dhtmlx_tasks = []
        for task in self.tasks:
            start_date_str = datetime.datetime.fromisoformat(task['start']).strftime("%Y-%m-%d")
            # For milestones, end_date might not be needed in the same way, but we ensure it exists
            end_date_str = datetime.datetime.fromisoformat(task.get('end', task['start'])).strftime("%Y-%m-%d")

            task_data = {
                'id': task['id'],
                'text': task['name'],
                'start_date': start_date_str,
                'color': self._get_dhtmlx_color(task['status'])
            }

            if task.get('type') == 'milestone':
                task_data['type'] = 'milestone'
                # Milestones in dhtmlxGantt are often represented by their start date.
                # Duration can be 0.
                task_data['duration'] = 0
            else:
                task_data['end_date'] = end_date_str
                task_data['progress'] = task.get('progress', 0)

            if task.get('due_date'):
                task_data['due_date_marker'] = datetime.datetime.fromisoformat(task['due_date']).strftime("%Y-%m-%d")
            
            dhtmlx_tasks.append(task_data)

        tasks_json = json.dumps(dhtmlx_tasks)

        # HTML template with DHTMLX Gantt configuration
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gantt Chart</title>
            <script src="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.js"></script>
            <link href="https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.css" rel="stylesheet">
            <!-- Include the QWebChannel script -->
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                html, body {
                    height: 100%;
                    padding: 0;
                    margin: 0;
                    overflow: hidden;
                    font-family: 'Segoe UI', sans-serif;
                }
                /* Make text inside tasks visible */
                .gantt_task_text { color: #fff; }

                /* Style for the progress bar text */
                .gantt_task_progress_text {
                    text-align: center;
                    font-weight: bold;
                    color: white;
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
                }

                /* Custom style for milestone tasks to look like diamonds */
                .gantt_milestone {
                    background-color: #d33daf !important; /* Distinct color for milestones */
                    border: 1px solid #a62a88;
                    transform: rotate(45deg);
                    box-shadow: 0 0 5px rgba(0,0,0,0.3);
                    border-radius: 2px;
                }
                
                /* Adjust the content box for milestones so it doesn't rotate with the box if we had any */
                .gantt_milestone .gantt_task_content {
                    display: none;
                }

                /* Progress bar styling */
                .gantt_task_progress {
                    background-color: rgba(0, 0, 0, 0.4); /* Dark overlay for progress */
                    border-radius: 2px;
                }
                
                /* Ensure the task bar itself has rounded corners */
                .gantt_task_line {
                    border-radius: 4px;
                    border: none;
                }

            </style>
        </head>
        <body>
            <div id="gantt_here" style='width:100%; height:100%;'></div>
            <script>
                document.addEventListener("DOMContentLoaded", function() {
                    // --- Initialize Web Channel ---
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.ganttBridge = channel.objects.ganttBridge;
                    });

                    // --- Gantt Configuration ---
                    gantt.config.date_format = "%Y-%m-%d";
                    gantt.config.readonly = false; // Make it interactive
                    gantt.config.show_errors = true;
                    gantt.config.drag_move = true;
                    gantt.config.drag_resize = true;
                    gantt.config.types.milestone = "milestone"; // Ensure milestone type is recognized
                    gantt.config.sort = true;
                    
                    // Adjust scale to be more readable
                    gantt.config.scale_height = 50;
                    gantt.config.scales = [
                        {unit: "month", step: 1, format: "%F, %Y"},
                        {unit: "day", step: 1, format: "%j, %D"}
                    ];

                    // --- Template for progress text ---
                    gantt.templates.progress_text = function(start, end, task){
                        if (task.progress) {
                            return Math.round(task.progress * 100) + "%";
                        }
                        return "";
                    };

                    // --- Template for task text ---
                    gantt.templates.task_text = function(start, end, task){
                        if (task.type == 'milestone') {
                            return ""; // No text inside the diamond
                        }
                        return "<b>" + task.text + "</b>";
                    };
                    
                    // --- Tooltip for milestones to show name ---
                    gantt.templates.tooltip_text = function(start, end, task){
                        return "<b>Task:</b> "+task.text+"<br/><b>Start:</b> "+gantt.templates.tooltip_date_format(start)+"<br/><b>End:</b> "+gantt.templates.tooltip_date_format(end);
                    };

                    // --- Template for task CSS class ---
                    gantt.templates.task_class = function(start, end, task){
                        var css = [];
                        if(task.type == 'milestone'){
                            css.push("gantt_milestone");
                        }
                        if(task.progress == 1){
                            css.push("task-completed"); 
                        }
                        return css.join(" ");
                    };
                    
                    // --- Event Handlers ---
                    gantt.attachEvent("onAfterTaskDrag", function(id, mode, task, original){
                        if (window.ganttBridge) {
                            var start_str = gantt.templates.format_date(task.start_date, "yyyy-MM-dd HH:mm");
                            var end_str = gantt.templates.format_date(task.end_date, "yyyy-MM-dd HH:mm");
                            window.ganttBridge.update_task_dates(id, start_str, end_str);
                        }
                    });

                    // --- Initialization ---
                    gantt.init("gantt_here");
                    gantt.parse({
                        data: __TASKS_JSON__
                    });
                });
            </script>
        </body>
        </html>
        '''
        
        return html_template.replace('__TASKS_JSON__', tasks_json)

    def export_to_html(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Gantt Chart to HTML", "", "HTML Files (*.html);;All Files (*)")
        if file_path:
            self.web_view.page().toHtml(lambda html_content: self._save_html_to_file(file_path, html_content))

    def _save_html_to_file(self, file_path, html_content):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"Gantt chart exported to {file_path}")
        except Exception as e:
            logging.error(f"Error exporting Gantt chart: {e}", exc_info=True)

    def export_to_png(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Gantt Chart to PNG", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            pixmap = self.web_view.grab()
            pixmap.save(file_path, 'png')
            logging.info(f"Gantt chart exported to {file_path}")