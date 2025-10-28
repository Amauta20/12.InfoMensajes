import pytest
import sqlite3
import datetime
from unittest.mock import patch

from app.db.database import create_schema, get_db_connection
from app.db.kanban_manager import KanbanManager
from app.search import search_manager # Needed for rebuild_fts_indexes
from app.utils import time_utils
from app.ui.gantt_chart_widget import GanttBridge

# Re-use the test_db fixture from other tests
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
    
    # Patch the get_db_connection in database module
    monkeypatch.setattr('app.db.database.get_db_connection', lambda: conn)

    create_schema(conn)
    search_manager.rebuild_fts_indexes()
    
    yield conn

def test_gantt_bridge_updates_card_dates(test_db):
    """Tests if the GanttBridge correctly updates card dates in the database."""
    conn = test_db # Get the connection from the fixture
    kanban_manager_instance = KanbanManager(conn) # Instantiate the manager

    kanban_manager_instance.create_default_columns()
    todo_col_id = kanban_manager_instance.get_all_columns()[0]['id']

    # 1. Create a card
    card_id = kanban_manager_instance.create_card(
        column_id=todo_col_id,
        title="Test Card for Bridge"
    )

    # 2. Instantiate the bridge with the manager
    bridge = GanttBridge(kanban_manager_instance)

    # 3. Simulate a call from JavaScript
    new_start_str = "2025-10-20 10:00"
    new_end_str = "2025-10-25 16:00"
    bridge.update_task_dates(card_id, new_start_str, new_end_str)

    # 4. Fetch the card again to verify
    updated_card = kanban_manager_instance.get_card_details(card_id)

    # 5. Assert the dates were updated correctly
    assert updated_card is not None
    
    # The bridge converts the string to a datetime object, which the db manager
    # then converts to a UTC ISO string. We need to compare timezone-aware objects.
    expected_start_dt = time_utils.to_utc(datetime.datetime.strptime(new_start_str, "%Y-%m-%d %H:%M"))
    expected_end_dt = time_utils.to_utc(datetime.datetime.strptime(new_end_str, "%Y-%m-%d %H:%M"))

    actual_start_dt = datetime.datetime.fromisoformat(updated_card['start_date'])
    actual_end_dt = datetime.datetime.fromisoformat(updated_card['end_date'])

    assert actual_start_dt == expected_start_dt
    assert actual_end_dt == expected_end_dt
