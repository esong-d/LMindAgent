import secrets


def generate_secret_key():
    key = secrets.token_hex(32)  # 64字符hex = 256bit
    return key


if __name__ == '__main__':
    print(generate_secret_key())