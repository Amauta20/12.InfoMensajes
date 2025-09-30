import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.db.database import create_schema
from app.security.vault import Vault
from app.ui.styles import dark_theme_stylesheet

# Workaround for QtWebEngine GPU issues
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-gpu-compositing --disable-gpu-rasterization --no-sandbox"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_ARGUMENTS"] = "--use-angle=d3d11"
os.environ["QT_OPENGL"] = "software"

def test_vault():
    print("\n--- Testing Vault --- ")
    secret_id = "test_api_key"
    plaintext = "my_super_secret_api_key_123"
    correct_passphrase = "my_master_password"
    incorrect_passphrase = "wrong_password"

    vault_instance = Vault() # Create an instance of Vault
    # Save secret
    vault_instance.save_secret(secret_id, plaintext, correct_passphrase)
    print(f"Secret '{secret_id}' saved.")

    # Retrieve with correct passphrase
    retrieved_secret = vault_instance.get_secret(secret_id, correct_passphrase)
    print(f"Retrieved with correct passphrase: {retrieved_secret}")
    assert retrieved_secret == plaintext

    # Retrieve with incorrect passphrase
    retrieved_secret_wrong = vault_instance.get_secret(secret_id, incorrect_passphrase)
    print(f"Retrieved with incorrect passphrase: {retrieved_secret_wrong}")
    assert retrieved_secret_wrong is None
    print("--- Vault Test Complete ---\n")

def main():
    # Ensure the database schema is created on startup
    create_schema()

    db_path = os.path.join(os.getcwd(), "infomensajero.db")
    print(f"Checking for database at: {db_path}")
    if os.path.exists(db_path):
        print("Database file found.")
    else:
        print("Database file NOT found.")
    
    test_vault() # Run vault test

    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_stylesheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
