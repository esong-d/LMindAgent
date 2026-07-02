

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import os
import jwt
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from app.core.config import get_settings

settings = get_settings()


def encrypt_password(password: str) -> tuple[str, str]:
    """
    :param password: 密码
    :return: 加密后的密码, 盐值
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 1_000_000)

    return base64.b64encode(key).decode('utf-8'), base64.b64encode(salt).decode('utf-8')


def verify_password(password: str, encrypted: str, salt: str) -> bool:
    """
    :param password: 密码
    :param encrypted: 加密后的密码
    :param salt: 盐值
    :return: 验证结果
    """
    salt_bytes = base64.b64decode(salt)
    key_bytes = base64.b64decode(encrypted)
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 1_000_000)
    return new_key == key_bytes


async def generate_jwt_token(user_id: int, expire: int = None) -> str:
    """
    :param user_info: 用户信息
    :param expire: 过期时间(seconds/秒), 如果为None则使用配置中的默认时间
    :return: token
    """
    if expire is None:
        expire = settings.jwt_expire

    _now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": _now + timedelta(seconds=expire), 
        "iat": _now,
        "type": "access"
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return token


async def refresh_jwt_token(user_id: int, expire: int = None) -> str:
    """
    :param user_info: 用户信息
    :param expire: 过期时间(seconds/秒), 如果为None则使用配置中的默认时间
    :return: token
    """
    return await generate_jwt_token(user_id, expire)


async def verify_jwt_token(token: str) -> dict | None:
    """
    :param token: token
    :return: payload
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


class AESCipher:
    def __init__(self, env_name: str = "MASTER_KEY"):
        key_hex = settings.aes_key_hex
        if not key_hex:
            raise ValueError(f"Environment variable {env_name} is not set")

        self.key = bytes.fromhex(key_hex)
        if len(self.key) not in (16, 24, 32):
            raise ValueError("MASTER_KEY must be 16/24/32 bytes in hex form")

    @staticmethod
    def generate_key_hex() -> str:
        # 32 bytes = AES-256
        return get_random_bytes(32).hex()

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        instance = cls()
        nonce = get_random_bytes(16)
        cipher = AES.new(instance.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

        # 存储格式: nonce + tag + ciphertext
        encrypted_data = nonce + tag + ciphertext
        return base64.b64encode(encrypted_data).decode("utf-8")

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        instance = cls()
        encrypted_data = base64.b64decode(encrypted_text.encode("utf-8"))

        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]

        cipher = AES.new(instance.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode("utf-8")


def md5(text: str | bytes) -> str:
    """
    :param text: 文本
    :return: md5值
    """
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.md5(text).hexdigest()