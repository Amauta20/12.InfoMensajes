
import pytest
import sqlite3
from unittest.mock import patch
import datetime
import time

from app.db.database import create_schema
from app.services import service_manager
from app.metrics.metrics_manager import MetricsManager

@pytest.fixture(autouse=True)
def test_db(monkeypatch):
    """Fixture to set up a single in-memory DB for all tests and patch connections."""
    class TestConnection(sqlite3.Connection):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.row_factory = sqlite3.Row

        def close(self):
            pass # Do nothing during tests

    conn = sqlite3.connect(":memory:", factory=TestConnection)
    
    # Patch the get_db_connection in all modules that use it
    monkeypatch.setattr('app.db.database.get_db_connection', lambda: conn)
    monkeypatch.setattr('app.db.notes_manager.get_db_connection', lambda: conn)
    monkeypatch.setattr('app.db.kanban_manager.get_db_connection', lambda: conn)
    monkeypatch.setattr('app.search.search_manager.get_db_connection', lambda: conn)
    monkeypatch.setattr('app.services.service_manager.get_db_connection', lambda: conn)
    monkeypatch.setattr('app.metrics.metrics_manager.get_db_connection', lambda: conn)

    create_schema()
    
    yield conn

@pytest.fixture
def metrics_manager_instance(test_db):
    """Provides a fresh MetricsManager instance for each test."""
    # Ensure the singleton is reset for each test
    MetricsManager._master_instance = None
    manager = MetricsManager.get_instance()
    manager._ensure_internal_services_exist() # Ensure internal services are created
    return manager

def test_metrics_tracking_single_service(metrics_manager_instance):
    """Tests tracking for a single service."""
    manager = metrics_manager_instance
    service_name = "Notas"

    manager.start_tracking(service_name)
    time.sleep(1.1) # Simulate some usage
    manager.stop_tracking_current()

    conn = service_manager.get_db_connection()
    cursor = conn.cursor()
    service_id = service_manager.get_service_by_name(service_name)['id']
    today_str = datetime.date.today().isoformat()

    cursor.execute("SELECT milliseconds FROM usage_metrics WHERE service_id = ? AND day = ?", (service_id, today_str))
    result = cursor.fetchone()

    assert result is not None
    assert result['milliseconds'] > 0

def test_metrics_tracking_multiple_services(metrics_manager_instance):
    """Tests tracking when switching between multiple services."""
    manager = metrics_manager_instance
    service_name_1 = "Kanban"
    service_name_2 = "Bóveda"

    manager.start_tracking(service_name_1)
    time.sleep(1.1)
    manager.start_tracking(service_name_2) # Switches from service 1 to service 2
    time.sleep(1.1)
    manager.stop_tracking_current()

    conn = service_manager.get_db_connection()
    cursor = conn.cursor()
    service_id_1 = service_manager.get_service_by_name(service_name_1)['id']
    service_id_2 = service_manager.get_service_by_name(service_name_2)['id']
    today_str = datetime.date.today().isoformat()

    cursor.execute("SELECT milliseconds FROM usage_metrics WHERE service_id = ? AND day = ?", (service_id_1, today_str))
    result_1 = cursor.fetchone()
    cursor.execute("SELECT milliseconds FROM usage_metrics WHERE service_id = ? AND day = ?", (service_id_2, today_str))
    result_2 = cursor.fetchone()

    assert result_1 is not None
    assert result_1['milliseconds'] > 0
    assert result_2 is not None
    assert result_2['milliseconds'] > 0

def test_metrics_no_tracking_for_short_duration(metrics_manager_instance):
    """Tests that very short durations are not logged."""
    manager = metrics_manager_instance
    service_name = "Gantt"

    manager.start_tracking(service_name)
    time.sleep(0.01) # Less than 1 second
    manager.stop_tracking_current()

    conn = service_manager.get_db_connection()
    cursor = conn.cursor()
    service_id = service_manager.get_service_by_name(service_name)['id']
    today_str = datetime.date.today().isoformat()

    cursor.execute("SELECT milliseconds FROM usage_metrics WHERE service_id = ? AND day = ?", (service_id, today_str))
    result = cursor.fetchone()

    assert result is None # Should not be logged
