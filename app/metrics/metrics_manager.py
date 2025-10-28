import datetime
# from app.db.database import get_db_connection # No longer needed directly
from app.services.service_manager import ServiceManager # Import the class

class MetricsManager:
    _master_instance = None # Use a different name to avoid confusion with _instance

    def __init__(self, conn):
        self.conn = conn
        self.service_manager = ServiceManager(self.conn) # Instantiate ServiceManager
        self.active_service_id = None
        self.session_start_time = None
        self._ensure_internal_services_exist()

    @classmethod
    def get_instance(cls, conn=None):
        if cls._master_instance is None:
            if conn is None:
                raise ValueError("Connection must be provided on first call to MetricsManager.get_instance()")
            cls._master_instance = cls(conn) # Pass conn to constructor
        return cls._master_instance

    def _ensure_internal_services_exist(self):
        """Ensures that internal tools like Notes, Kanban, etc., have service entries."""
        internal_tools = [
            ("Notas", "internal://notes", "notes_icon.png"),
            ("Kanban", "internal://kanban", "kanban_icon.png"),
            ("Gantt", "internal://gantt", "gantt_icon.png"),
            ("Checklist", "internal://checklist", "checklist_icon.png"),
            ("Recordatorios", "internal://reminders", "reminders_icon.png"),
            ("Lector RSS", "internal://rss", "rss_icon.png"),
            ("Bóveda", "internal://vault", "vault_icon.png"),
            ("Pomodoro", "internal://pomodoro", "pomodoro_icon.png"),
            ("Búsqueda", "internal://search", "search_icon.png"),
            ("Bienvenida", "internal://welcome", "welcome_icon.png"),
        ]
        for name, url, icon in internal_tools:
            if not self.service_manager.get_service_by_name(name):
                self.service_manager.add_service(name, url, icon, is_internal=True)

    def start_tracking(self, service_name: str):
        """Starts tracking usage for a given service/tool name."""
        self.stop_tracking_current() # Ensure previous session is logged

        service = self.service_manager.get_service_by_name(service_name)
        if service:
            self.active_service_id = service['id']
            self.session_start_time = datetime.datetime.now()
        else:
            print(f"Warning: Service '{service_name}' not found for tracking.")

    def stop_tracking_current(self):
        """Stops tracking the current active service and logs the duration."""
        if self.active_service_id is not None and self.session_start_time is not None:
            duration = datetime.datetime.now() - self.session_start_time
            milliseconds = int(duration.total_seconds() * 1000)
            
            if milliseconds > 1000: # Only log if duration is more than 1 second
                self._log_usage(self.active_service_id, milliseconds)

        self.active_service_id = None
        self.session_start_time = None

    def _log_usage(self, service_id: int, milliseconds: int):
        """Logs the usage data to the database."""
        cursor = self.conn.cursor()
        today_str = datetime.date.today().isoformat() # YYYY-MM-DD

        # Check if an entry for today already exists for this service
        cursor.execute(
            "SELECT id, milliseconds FROM usage_metrics WHERE service_id = ? AND day = ?",
            (service_id, today_str)
        )
        existing_entry = cursor.fetchone()

        if existing_entry:
            # Update existing entry
            new_milliseconds = existing_entry['milliseconds'] + milliseconds
            cursor.execute(
                "UPDATE usage_metrics SET milliseconds = ? WHERE id = ?",
                (new_milliseconds, existing_entry['id'])
            )
        else:
            # Insert new entry
            cursor.execute(
                "INSERT INTO usage_metrics (service_id, milliseconds, day) VALUES (?, ?, ?)",
                (service_id, milliseconds, today_str)
            )
        self.conn.commit()
