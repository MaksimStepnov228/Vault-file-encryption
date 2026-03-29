import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

SALT_SIZE  = 32
NONCE_SIZE = 12
ITERATIONS = 600_000

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode())

def encrypt_file(input_path: str, output_path: str, password: str, progress=None):
    def p(val, msg=""):
        if progress:
            progress(val, msg)

    p(0.05, "Reading file...")
    with open(input_path, 'rb') as f:
        plaintext = f.read()

    p(0.15, "Generating salt & nonce...")
    salt  = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    p(0.20, "Deriving key (this takes a moment)...")
    key = derive_key(password, salt)

    p(0.80, "Encrypting...")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)

    p(0.95, "Writing output file...")
    with open(output_path, 'wb') as f:
        f.write(salt + nonce + ciphertext)

    p(1.00, "Done.")

def decrypt_file(input_path: str, output_path: str, password: str, progress=None):
    def p(val, msg=""):
        if progress:
            progress(val, msg)

    p(0.05, "Reading file...")
    with open(input_path, 'rb') as f:
        data = f.read()

    salt       = data[:SALT_SIZE]
    nonce      = data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = data[SALT_SIZE + NONCE_SIZE:]

    p(0.20, "Getting key (this takes a moment)...")
    key = derive_key(password, salt)

    p(0.80, "Decrypting & checking file contents...")
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError("Wrong password or file has been tampered with.")

    p(0.95, "Writing output file...")
    with open(output_path, 'wb') as f:
        f.write(plaintext)

    p(1.00, "Done.")