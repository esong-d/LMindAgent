import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.security import AESCipher


def test_aes():
    key_hex = AESCipher.generate_key_hex()
    print("Generated AES Key (hex):", key_hex)


if __name__ == "__main__":
    test_aes()
