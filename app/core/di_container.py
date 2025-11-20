import sqlite3
from app.db.database import get_db_connection
from app.db.settings_manager import SettingsManager
from app.metrics.metrics_manager import MetricsManager
from app.db.notes_manager import NotesManager
from app.db.kanban_manager import KanbanManager
from app.db.checklist_manager import ChecklistManager
from app.db.reminders_manager import RemindersManager
from app.security.vault_manager import VaultManager
from app.services.service_manager import ServiceManager
from app.search.search_manager import SearchManager
from app.services_layer.kanban_service import KanbanService
from app.services_layer.notes_service import NotesService
from app.services_layer.checklist_service import ChecklistService
from app.services_layer.reminders_service import RemindersService
from app.ai.ai_manager import AIManager
from app.security.app_security_manager import AppSecurityManager
from app.automation.rules_manager import RulesManager
from app.automation.templates_manager import TemplatesManager
from app.ui.theme_manager import ThemeManager

class DIContainer:
    _instance = None

    def __init__(self, db_path=None):
        if DIContainer._instance is not None:
            raise Exception("This class is a singleton!")
        
        self.db_path = db_path
        self.conn = None
        
        # Managers
        self.settings_manager = None
        self.metrics_manager = None
        self.vault_manager = None
        self.service_manager = None
        self.search_manager = None
        self.notes_manager = None
        self.kanban_manager = None
        self.checklist_manager = None
        self.reminders_manager = None
        self.app_security_manager = None
        self.rules_manager = None
        self.templates_manager = None
        self.theme_manager = None
        
        # Services Layer
        self.kanban_service = None
        self.notes_service = None
        self.checklist_service = None
        self.reminders_service = None

        self._initialize()

    @classmethod
    def initialize(cls, db_path=None):
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("DIContainer not initialized.")
        return cls._instance

    def _initialize(self):
        # 1. Database Connection
        self.conn = get_db_connection(self.db_path)

        # 2. Core Managers (Low level)
        SettingsManager.initialize(self.conn)
        self.settings_manager = SettingsManager.get_instance()
        
        self.metrics_manager = MetricsManager.get_instance(self.conn)
        self.vault_manager = VaultManager(self.conn)
        self.service_manager = ServiceManager(self.conn)
        self.search_manager = SearchManager(self.conn)
        self.app_security_manager = AppSecurityManager(self.settings_manager)
        self.theme_manager = ThemeManager(self.settings_manager)

        # 3. Feature Managers
        self.notes_manager = NotesManager(self.conn)
        self.kanban_manager = KanbanManager(self.conn)
        self.checklist_manager = ChecklistManager(self.conn)
        self.reminders_manager = RemindersManager(self.conn)

        # 4. Services Layer (Business Logic)
        self.kanban_service = KanbanService(self.kanban_manager)
        self.notes_service = NotesService(self.notes_manager)
        self.checklist_service = ChecklistService(self.checklist_manager)
        # Reminders service depends on kanban and checklist services
        self.reminders_service = RemindersService(
            self.reminders_manager, 
            self.kanban_service, 
            self.checklist_service
        )

        # 5. AI Manager (depends on Settings and Vault)
        # 5. AI Manager (depends on Settings and Vault)
        AIManager.initialize(self.settings_manager, self.vault_manager)

        # 6. Automation Managers
        self.rules_manager = RulesManager(self.conn)
        self.templates_manager = TemplatesManager(self.conn)

    def close(self):
        if self.conn:
            self.conn.close()
