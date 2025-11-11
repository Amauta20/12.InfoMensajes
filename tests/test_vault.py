import pytest
import sqlite3
import os
from app.security.vault import Vault
from app.security.vault_manager import VaultManager
from app.db.database import create_schema

@pytest.fixture
def in_memory_db_connection():
    """Provides an in-memory SQLite database connection with schema created."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    yield conn
    conn.close()

@pytest.fixture
def vault_manager_instance(in_memory_db_connection):
    """Provides a VaultManager instance with an in-memory database."""
    manager = VaultManager()
    manager.set_conn(in_memory_db_connection)
    # Ensure it's locked initially for each test
    manager.lock()
    return manager

# --- Tests for VaultManager functionality ---

def test_vault_manager_initial_locked_state(vault_manager_instance):
    """Test that the vault manager is locked initially."""
    assert vault_manager_instance.is_locked()

def test_vault_manager_unlock_new_vault_success(vault_manager_instance):
    """Test unlocking a new vault (no test secret exists yet)."""
    master_passphrase = "my_super_secret_password"
    assert vault_manager_instance.unlock(master_passphrase)
    assert not vault_manager_instance.is_locked()

def test_vault_manager_unlock_existing_vault_correct_passphrase(vault_manager_instance):
    """Test unlocking an existing vault with the correct passphrase."""
    master_passphrase = "my_super_secret_password"
    # First, unlock and save the test secret
    vault_manager_instance.unlock(master_passphrase)
    vault_manager_instance.lock() # Lock it again to test unlocking an existing one

    assert vault_manager_instance.unlock(master_passphrase)
    assert not vault_manager_instance.is_locked()

def test_vault_manager_unlock_existing_vault_wrong_passphrase(vault_manager_instance):
    """Test unlocking an existing vault with an incorrect passphrase."""
    master_passphrase = "my_super_secret_password"
    wrong_passphrase = "wrong_password"

    # First, unlock and save the test secret
    vault_manager_instance.unlock(master_passphrase)
    vault_manager_instance.lock()

    assert not vault_manager_instance.unlock(wrong_passphrase)
    assert vault_manager_instance.is_locked()

def test_vault_manager_lock(vault_manager_instance):
    """Test locking the vault."""
    master_passphrase = "my_super_secret_password"
    vault_manager_instance.unlock(master_passphrase)
    assert not vault_manager_instance.is_locked()
    vault_manager_instance.lock()
    assert vault_manager_instance.is_locked()

def test_vault_manager_save_and_get_secret_success(vault_manager_instance):
    """Test saving and retrieving a secret with the vault manager."""
    master_passphrase = "my_super_secret_password"
    secret_id = "api_key"
    plaintext = "sk-1234567890abcdef"

    vault_manager_instance.unlock(master_passphrase)
    vault_manager_instance.save_secret(secret_id, plaintext)
    retrieved_secret = vault_manager_instance.get_secret(secret_id)

    assert retrieved_secret == plaintext

def test_vault_manager_get_secret_not_found(vault_manager_instance):
    """Test retrieving a non-existent secret."""
    master_passphrase = "my_super_secret_password"
    vault_manager_instance.unlock(master_passphrase)
    retrieved_secret = vault_manager_instance.get_secret("non_existent_id")
    assert retrieved_secret is None

def test_vault_manager_access_locked_vault_raises_permission_error(vault_manager_instance):
    """Test that accessing a locked vault raises a PermissionError."""
    # Vault is locked by default from fixture
    with pytest.raises(PermissionError):
        vault_manager_instance.save_secret("test_id", "test_secret")
    with pytest.raises(PermissionError):
        vault_manager_instance.get_secret("test_id")
    with pytest.raises(PermissionError):
        vault_manager_instance.get_all_secret_ids()
    with pytest.raises(PermissionError):
        vault_manager_instance.delete_secret("test_id")

def test_vault_manager_update_secret(vault_manager_instance):
    """Test updating an existing secret."""
    master_passphrase = "my_super_secret_password"
    secret_id = "config_token"
    initial_plaintext = "old_token"
    updated_plaintext = "new_token"

    vault_manager_instance.unlock(master_passphrase)
    vault_manager_instance.save_secret(secret_id, initial_plaintext)
    assert vault_manager_instance.get_secret(secret_id) == initial_plaintext

    vault_manager_instance.save_secret(secret_id, updated_plaintext) # Update
    assert vault_manager_instance.get_secret(secret_id) == updated_plaintext

def test_vault_manager_delete_secret(vault_manager_instance):
    """Test deleting a secret."""
    master_passphrase = "my_super_secret_password"
    secret_id = "temp_secret"
    plaintext = "to_be_deleted"

    vault_manager_instance.unlock(master_passphrase)
    vault_manager_instance.save_secret(secret_id, plaintext)
    assert vault_manager_instance.get_secret(secret_id) == plaintext

    vault_manager_instance.delete_secret(secret_id)
    assert vault_manager_instance.get_secret(secret_id) is None

def test_vault_manager_get_all_secret_ids(vault_manager_instance):
    """Test retrieving all secret IDs."""
    master_passphrase = "my_super_secret_password"
    vault_manager_instance.unlock(master_passphrase)

    vault_manager_instance.save_secret("secret1", "value1")
    vault_manager_instance.save_secret("secret2", "value2")
    vault_manager_instance.save_secret("secret3", "value3")

    ids = vault_manager_instance.get_all_secret_ids()
    # The '_vault_test_' secret is excluded by get_all_secret_ids, so expect 3
    assert len(ids) == 3
    assert "secret1" in ids
    assert "secret2" in ids
    assert "secret3" in ids


    # Test after deleting one
    vault_manager_instance.delete_secret("secret2")
    ids_after_delete = vault_manager_instance.get_all_secret_ids()
    assert len(ids_after_delete) == 2
    assert "secret2" not in ids_after_delete
