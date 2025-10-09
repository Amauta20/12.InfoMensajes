import json
import os
import sqlite3
from app.db.database import get_db_connection

CATALOG_FILE = os.path.join(os.path.dirname(__file__), "catalog.json")
PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "profiles")

def load_catalog():
    """Loads the service catalog from JSON file."""
    if not os.path.exists(CATALOG_FILE):
        return []
    with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_services():
    """Retrieves all added services from the database."""
    conn = get_db_connection()
    services = conn.execute("SELECT * FROM services WHERE is_active = 1 ORDER BY name").fetchall()
    return services

def get_user_services():
    """Retrieves only user-added services (where is_internal is False)."""
    conn = get_db_connection()
    services = conn.execute("SELECT * FROM services WHERE is_active = 1 AND is_internal = 0 ORDER BY name").fetchall()
    return services

def add_service(name, url, icon=None, is_internal=False):
    """Adds a new service to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create a unique profile path for the service
    profile_name = f"service_{name.lower().replace(' ', '_')}"
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    
    # Ensure the profiles directory exists
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)

    try:
        cursor.execute(
            "INSERT INTO services (name, url, icon, profile_path, is_internal) VALUES (?, ?, ?, ?, ?)",
            (name, url, icon, profile_path, is_internal)
        )
        conn.commit()
        service_id = cursor.lastrowid
    except sqlite3.IntegrityError as e:
        # This could happen if the profile_path is not unique, which is unlikely
        # but good to handle.
        conn.rollback()
        print(f"Error adding service: {e}")
        return None
    finally:
        conn.close()
    
    return service_id

def get_service_by_name(name):
    """Retrieves full details of a service by its name."""
    conn = get_db_connection()
    service = conn.execute("SELECT id, name, url, icon, profile_path, is_internal FROM services WHERE name = ?", (name,)).fetchone()
    conn.close()
    return service

def get_service_by_profile_path(profile_path):
    """Retrieves full details of a service by its profile path."""
    conn = get_db_connection()
    service = conn.execute("SELECT id, name, url, icon, profile_path, is_internal FROM services WHERE profile_path = ?", (profile_path,)).fetchone()
    conn.close()
    return service

def delete_service(service_id):
    """Deletes a service from the database and removes its profile directory."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get profile path before deleting from DB
    cursor.execute("SELECT profile_path FROM services WHERE id = ?", (service_id,))
    row = cursor.fetchone()
    profile_path = row['profile_path'] if row else None

    cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
    conn.commit()
    # conn.close() # Managed by calling context

    # Remove profile directory if it exists
    if profile_path and os.path.exists(profile_path):
        try:
            import shutil
            shutil.rmtree(profile_path)
            print(f"Removed profile directory: {profile_path}")
        except OSError as e:
            print(f"Error removing profile directory {profile_path}: {e}")

def update_service_name(service_id, new_name):
    """Updates a service's name and renames its profile directory."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get old name and profile path
    cursor.execute("SELECT name, profile_path FROM services WHERE id = ?", (service_id,))
    row = cursor.fetchone()
    if not row: return False

    old_name = row['name']
    old_profile_path = row['profile_path']

    # Generate new profile path
    new_profile_name = f"service_{new_name.lower().replace(' ', '_')}"
    new_profile_path = os.path.join(PROFILES_DIR, new_profile_name)

    # Rename directory on file system
    if os.path.exists(old_profile_path) and old_profile_path != new_profile_path:
        try:
            os.rename(old_profile_path, new_profile_path)
            print(f"Renamed profile directory from {old_profile_path} to {new_profile_path}")
        except OSError as e:
            print(f"Error renaming profile directory: {e}")
            conn.close()
            return False

    # Update DB
    cursor.execute("UPDATE services SET name = ?, profile_path = ? WHERE id = ?", (new_name, new_profile_path, service_id))
    conn.commit()
    # conn.close() # Managed by calling context
    return service_id

def get_service_by_id(service_id):
    """Retrieves full details of a service by its ID."""
    conn = get_db_connection()
    service = conn.execute("SELECT id, name, url, icon, profile_path FROM services WHERE id = ?", (service_id,)).fetchone()
    conn.close()
    return service
