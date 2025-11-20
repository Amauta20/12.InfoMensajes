import sys
import os
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.settings_manager import SettingsManager

def test_settings_manager():
    print("Testing SettingsManager initialization...")
    conn = sqlite3.connect(":memory:")
    try:
        SettingsManager.initialize(conn)
        print("SettingsManager initialized successfully.")
        instance = SettingsManager.get_instance()
        print(f"Instance retrieved: {instance}")
    except Exception as e:
        print(f"Error initializing SettingsManager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_settings_manager()
