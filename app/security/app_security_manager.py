import hashlib
from app.db.settings_manager import SettingsManager

class AppSecurityManager:
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager

    def _hash_password(self, password: str) -> str:
        """Hashes a password using SHA256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def set_lock_password(self, password: str):
        """Sets the application lock password by storing its hash."""
        hashed_password = self._hash_password(password)
        self.settings_manager.set_app_lock_password_hash(hashed_password)

    def verify_lock_password(self, password: str) -> bool:
        """Verifies if the provided password matches the stored hash."""
        stored_hash = self.settings_manager.get_app_lock_password_hash()
        if not stored_hash:
            return False # No password set
        return self._hash_password(password) == stored_hash

    def is_lock_enabled(self) -> bool:
        """Checks if the application lock is enabled."""
        return self.settings_manager.get_app_lock_enabled()

    def set_lock_enabled(self, enabled: bool):
        """Enables or disables the application lock."""
        self.settings_manager.set_app_lock_enabled(enabled)

    def has_lock_password(self) -> bool:
        """Checks if an application lock password has been set."""
        return self.settings_manager.get_app_lock_password_hash() is not None
