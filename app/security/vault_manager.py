
from cryptography.exceptions import InvalidTag

from app.security.vault import Vault

class VaultManager:
    _instance = None
    _master_passphrase = None
    _vault = Vault()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VaultManager, cls).__new__(cls)
        return cls._instance

    def is_locked(self) -> bool:
        """Check if the vault is currently locked (i.e., no master passphrase set)."""
        return self._master_passphrase is None

    def unlock(self, passphrase: str) -> bool:
        """Tries to unlock the vault with the given passphrase.

        It does this by trying to decrypt a known test secret. If it succeeds,
        the passphrase is correct and is stored for the session.
        """
        # For a new vault, we might not have a test secret. Let's create one.
        # In a real scenario, this would be more robust.
        try:
            # Try to decrypt a test secret to verify the password
            test_secret = self._vault.get_secret('_vault_test_', passphrase)
            if test_secret is None:
                # If it doesn't exist, it's likely a new vault. Create it.
                self._vault.save_secret('_vault_test_', 'ok', passphrase)
                self._master_passphrase = passphrase
                return True
            elif test_secret == 'ok':
                self._master_passphrase = passphrase
                return True
            else:
                return False # Should not happen
        except InvalidTag:
            return False # Wrong password
        except Exception:
            return False # Other errors

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

# Global instance
vault_manager = VaultManager()
