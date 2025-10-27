from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
import os
import base64

from app.db.database import get_db_connection

# Scrypt parameters as per blueprint
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
KEY_LENGTH = 32 # AES-256

class Vault:
    def __init__(self, db_path):
        self.db_path = db_path

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        kdf = Scrypt(
            salt=salt,
            length=KEY_LENGTH,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            backend=default_backend()
        )
        return kdf.derive(passphrase.encode('utf-8'))

    def save_secret(self, secret_id: str, plaintext: str, passphrase: str):
        """Encrypts and saves a secret to the database."""
        salt = os.urandom(16) # Generate a random salt for KDF
        key = self._derive_key(passphrase, salt)
        nonce = os.urandom(12) # AES-GCM recommended nonce size is 12 bytes

        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

        # Store encrypted data, nonce, salt, and tag
        enc_blob = base64.b64encode(ciphertext + encryptor.tag).decode('utf-8')
        nonce_b64 = base64.b64encode(nonce).decode('utf-8')
        salt_b64 = base64.b64encode(salt).decode('utf-8')

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO credentials (id, enc_blob, nonce, salt) VALUES (?, ?, ?, ?)",
            (secret_id, enc_blob, nonce_b64, salt_b64)
        )
        conn.commit()
        conn.close()

    def get_secret(self, secret_id: str, passphrase: str) -> str | None:
        """Retrieves and decrypts a secret from the database."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT enc_blob, nonce, salt FROM credentials WHERE id = ?", (secret_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None # Secret not found

        enc_blob_b64, nonce_b64, salt_b64 = row['enc_blob'], row['nonce'], row['salt']

        enc_data_with_tag = base64.b64decode(enc_blob_b64)
        nonce = base64.b64decode(nonce_b64)
        salt = base64.b64decode(salt_b64)

        key = self._derive_key(passphrase, salt)

        # Separate ciphertext and tag
        ciphertext = enc_data_with_tag[:-16] # GCM tag is 16 bytes
        tag = enc_data_with_tag[-16:]

        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except InvalidTag:
            # Incorrect passphrase or corrupted data
            return None
        except Exception as e:
            print(f"Error decrypting secret: {e}")
            return None

    def get_all_secret_ids(self) -> list[str]:
        """Retrieves all secret IDs from the database, excluding internal ones."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM credentials WHERE id != '_vault_test_' ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [row['id'] for row in rows]

    def delete_secret(self, secret_id: str):
        """Deletes a secret from the database."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM credentials WHERE id = ?", (secret_id,))
        conn.commit()
        conn.close()