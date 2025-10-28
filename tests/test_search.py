
import pytest

import sqlite3

import os



from app.db.database import create_schema, get_db_connection

from app.db.notes_manager import NotesManager # Import the class

from app.db.kanban_manager import KanbanManager # Import the class

from app.search import search_manager





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

    monkeypatch.setattr('app.search.search_manager.get_db_connection', lambda: conn)

    monkeypatch.setattr('app.services.service_manager.get_db_connection', lambda: conn)

    monkeypatch.setattr('app.metrics.metrics_manager.get_db_connection', lambda: conn)



    create_schema(conn)

    search_manager.rebuild_fts_indexes()

    

    yield conn





def test_search_finds_note(test_db):

    """Tests that FTS can find content in a note."""

    conn = test_db

    notes_manager_instance = NotesManager(conn) # Instantiate manager



    notes_manager_instance.create_note("Esta es una nota sobre Python y desarrollo.")



    results = search_manager.search_all("Python")

    assert len(results) == 1

    assert results[0]['type'] == 'note'

    assert "Python" in results[0]['content']



def test_search_finds_kanban_card(test_db):

    """Tests that FTS can find content in a Kanban card's title and description."""

    conn = test_db

    kanban_manager_instance = KanbanManager(conn) # Instantiate manager



    kanban_manager_instance.create_default_columns()

    kanban_manager_instance.create_card(1, "Refactorizar el módulo de UI", "Se necesita optimizar el rendimiento.")



    # Search title

    results_title = search_manager.search_all("Refactorizar")

    assert len(results_title) == 1

    assert results_title[0]['type'] == 'kanban_card'

    assert results_title[0]['title'] == "Refactorizar el módulo de UI"



    # Search description

    results_desc = search_manager.search_all("rendimiento")

    assert len(results_desc) == 1

    assert results_desc[0]['type'] == 'kanban_card'



def test_search_no_results(test_db):

    """Tests that the search returns no results for a query that doesn't match."""

    conn = test_db

    notes_manager_instance = NotesManager(conn) # Instantiate manager



    notes_manager_instance.create_note("Nota de prueba.")



    results = search_manager.search_all("palabrainventada")

    assert len(results) == 0



def test_search_prefix(test_db):

    """Tests that FTS prefix search works correctly."""

    conn = test_db

    kanban_manager_instance = KanbanManager(conn) # Instantiate manager



    kanban_manager_instance.create_default_columns()

    kanban_manager_instance.create_card(1, "Implementar la autenticación", "Usar tokens JWT.")



    results = search_manager.search_all("autent") # Prefix of 'autenticación'

    assert len(results) == 1

    assert results[0]['type'] == 'kanban_card'
