import base64
from cryptography.fernet import Fernet
from .config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.fernet_key
    if not key:
        # Development fallback. In production, set FERNET_KEY from `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
        raw = settings.secret_key.encode()[:32].ljust(32, b'0')
        key = base64.urlsafe_b64encode(raw).decode()
    return Fernet(key.encode())


def encrypt_value(value: str) -> str:
    if not value:
        return ''
    return _fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return ''
    return _fernet().decrypt(value.encode()).decode()
