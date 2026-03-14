"""
Transparent field-level encryption for sensitive model fields.

Fields encrypted with this class store Fernet-encrypted bytes in the
database.  Existing plain-text values are returned as-is (backward
compatible) — they become encrypted next time the record is saved.

Configuration:
    Add to .env:
        FIELD_ENCRYPTION_KEY=<base64-url-safe 32-byte Fernet key>
    Generate a new key:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

If FIELD_ENCRYPTION_KEY is not set, the field behaves exactly like a
plain TextField — no encryption and no errors.  This ensures the app
stays operational even if the key is not yet configured.
"""

import logging

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

# Fernet-encrypted values always start with this prefix (base64 "gAAAAA")
_FERNET_PREFIX = "gAAAAA"


def _get_fernet():
    """Return a Fernet instance if FIELD_ENCRYPTION_KEY is configured."""
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        logger.error("EncryptedField: invalid FIELD_ENCRYPTION_KEY — encryption disabled: %s", exc)
        return None


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value.  Returns plaintext unchanged if key not set."""
    if not plaintext:
        return plaintext
    fernet = _get_fernet()
    if fernet is None:
        return plaintext
    try:
        return fernet.encrypt(plaintext.encode()).decode()
    except Exception as exc:
        logger.error("EncryptedField: encryption failed: %s", exc)
        return plaintext


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted string.

    * If the value looks like a Fernet token (starts with _FERNET_PREFIX),
      attempt decryption.
    * Otherwise return as-is (plain-text backward compatibility).
    * Returns the raw value on decryption failure so the app stays usable.
    """
    if not ciphertext:
        return ciphertext
    if not ciphertext.startswith(_FERNET_PREFIX):
        # Plain-text legacy value — return unchanged
        return ciphertext
    fernet = _get_fernet()
    if fernet is None:
        return ciphertext
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except Exception as exc:
        logger.error("EncryptedField: decryption failed (returning raw value): %s", exc)
        return ciphertext


class EncryptedCharField(models.TextField):
    """
    A TextField that transparently encrypts values on write and decrypts on
    read using Fernet symmetric encryption.

    Drop-in replacement for CharField / TextField.  Existing plain-text data
    remains readable and is encrypted automatically on the next save().

    Storage: TextField (no length limit — encrypted values are longer than
    the original).  Make sure your migration changes field type to TextField.
    """

    def from_db_value(self, value, expression, connection):
        """Decrypt when loading from the database."""
        return decrypt_value(value) if value else value

    def to_python(self, value):
        """Decrypt in forms / deserialization."""
        return decrypt_value(value) if value else value

    def get_prep_value(self, value):
        """Encrypt before writing to the database."""
        prepped = super().get_prep_value(value)
        return encrypt_value(prepped) if prepped else prepped
