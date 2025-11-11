from cryptography.exceptions import InvalidTag

from app.security.vault import Vault

class VaultManager:
    def __init__(self, conn):
        if conn is None:
            raise ValueError("Database connection cannot be None.")
        self._conn = conn
        self._vault = Vault(self._conn)
        self._master_passphrase = None

    def is_locked(self) -> bool:
        """Check if the vault is currently locked (i.e., no master passphrase set)."""
        return self._master_passphrase is None

    def unlock(self, passphrase: str) -> bool:
        """Tries to unlock the vault with the given passphrase.

        It does this by trying to decrypt a known test secret. If it succeeds,
        the passphrase is correct and is stored for the session.
        """
        # Check if the test secret exists in the database
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM credentials WHERE id = '_vault_test_'")
        test_secret_exists = cursor.fetchone() is not None

        if not test_secret_exists:
            # This is a new vault, create the test secret and unlock
            self._vault.save_secret('_vault_test_', 'ok', passphrase)
            self._master_passphrase = passphrase
            return True
        else:
            # Test secret exists, try to decrypt it to verify the passphrase
            try:
                test_secret_value = self._vault.get_secret('_vault_test_', passphrase)
                if test_secret_value == 'ok':
                    self._master_passphrase = passphrase
                    return True
                else:
                    # Decryption failed or returned something other than 'ok'
                    return False
            except InvalidTag:
                # Incorrect passphrase
                return False
            except Exception:
                # Other errors during decryption
                return False

    def lock(self):
        """Locks the vault by clearing the master passphrase from memory."""
        self._master_passphrase = None

    def save_secret(self, secret_id: str, plaintext: str):
        if self.is_locked():
            raise PermissionError("Vault is locked.")
        self._vault.save_secret(secret_id, plaintext, self._master_passphrase)

    def get_secret(self, secret_id: str) -> str | None:
        if self.is_locked():
            raise PermissionError("Vault is locked.")
        return self._vault.get_secret(secret_id, self._master_passphrase)

    def get_all_secret_ids(self) -> list[str]:
        if self.is_locked():
            raise PermissionError("Vault is locked.")
        return self._vault.get_all_secret_ids()

    def delete_secret(self, secret_id: str):
        if self.is_locked():
            raise PermissionError("Vault is locked.")
        self._vault.delete_secret(secret_id)

    def change_master_passphrase(self, old_passphrase: str, new_passphrase: str):
        if self.is_locked():
            # This should not happen if unlock is called before, but as a safeguard
            raise PermissionError("Vault is locked. Unlock with old passphrase first.")
        
        # Re-encrypt all secrets with the new passphrase
        self._vault.change_passphrase(old_passphrase, new_passphrase)
        
        # Update the in-memory master passphrase
        self._master_passphrase = new_passphrase
