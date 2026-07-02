# 生成aes key
import os

from app.core.security import AESCipher


def generate_aes_key():
    cipher = AESCipher.generate_key_hex()
    return cipher


if __name__ == "__main__":
    key = generate_aes_key()
    print("Generated AES Key (hex):", key)
    