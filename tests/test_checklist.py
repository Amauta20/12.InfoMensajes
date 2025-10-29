import pytest
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import get_db_connection, create_schema
from app.db.settings_manager import SettingsManager
from app.ui.checklist_widget import ChecklistWidget, AddChecklistItemDialog

def test_add_checklist_item(qtbot, mocker):
    # Ensure a QApplication instance exists
    app = QApplication.instance() or QApplication([])

    # Initialize SettingsManager for the test
    conn = get_db_connection(':memory:')
    create_schema(conn)
    SettingsManager.initialize(conn)

    # Mock the dialog to avoid GUI interaction
    mocker.patch.object(AddChecklistItemDialog, 'exec', return_value=AddChecklistItemDialog.DialogCode.Accepted)
    mocker.patch.object(AddChecklistItemDialog, 'getItemData', return_value=('Test Item', None))

    # Create the widget
    widget = ChecklistWidget(settings_manager=mocker.MagicMock(), conn=conn)
    qtbot.addWidget(widget)

    # Switch to the independent checklists tab
    widget.tab_widget.setCurrentIndex(1)

    # Add an independent checklist
    checklist_name = "Test Checklist"
    # Mock QInputDialog.getText to return a checklist name
    mocker.patch('PyQt6.QtWidgets.QInputDialog.getText', return_value=(checklist_name, True))
    widget.add_independent_checklist()

    # Find and select the new checklist
    new_checklist_id = None
    for i in range(widget.independent_checklist_list.count()):
        item = widget.independent_checklist_list.item(i)
        if item.text() == checklist_name:
            new_checklist_id = item.data(Qt.ItemDataRole.UserRole)
            widget.independent_checklist_list.setCurrentItem(item)
            widget.on_independent_checklist_selected(item)
            break
    assert new_checklist_id is not None
    
    # Add an item to the checklist
    widget.add_item()

    # Assert that the item is in the list
    assert widget.independent_checklist_items_list.count() == 1
    
    # Get the widget for the first item
    list_item = widget.independent_checklist_items_list.item(0)
    item_widget = widget.independent_checklist_items_list.itemWidget(list_item)
    
    # Find the QLabel that displays the item text
    label = item_widget.findChild(QLabel)
    
    assert label is not None
    assert label.text() == 'Test Item'