import base64
import hashlib
from cryptography.fernet import Fernet

def get_key_from_answer(answer: str):
    """
    Derive a Fernet key from the receiver's answer.
    """
    hashed = hashlib.sha256(answer.encode()).digest()
    return base64.urlsafe_b64encode(hashed[:32])

def encrypt_file(file_bytes: bytes, answer: str) -> bytes:
    key = get_key_from_answer(answer)
    f = Fernet(key)
    return f.encrypt(file_bytes)

def decrypt_file(encrypted_bytes: bytes, answer: str) -> bytes:
    key = get_key_from_answer(answer)
    f = Fernet(key)
    return f.decrypt(encrypted_bytes)
