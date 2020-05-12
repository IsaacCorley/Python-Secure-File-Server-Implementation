import os
import json
from typing import Tuple
from base64 import b64decode, b64encode

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_v1_5, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad



def generate_keys(bits: int = 2048, e: int = 65535) -> Tuple[bytes, bytes]:
    """ Generate public and private keys for RSA crypto """
    key = RSA.generate(bits=bits, e=e)
    return key.publickey().export_key(), key.export_key()

def export_keys(key_dir: str, user: str, pub_key: bytes, priv_key: bytes):
    """ Export keys to files for user """
    with open(os.path.join(key_dir, user + "_private.pem"), "wb") as f:
        f.write(priv_key)

    with open(os.path.join(key_dir, user + "_public.pem"), "wb") as f:
        f.write(pub_key)


def rsa_encrypt(data: bytes, pub_key: str, priv_key: str) -> Tuple[str, str]:
    """ Encrypt via RSA """
    # Ciphertext
    key = RSA.import_key(pub_key)
    cipher = PKCS1_v1_5.new(key)
    ciphertext = cipher.encrypt(data)

    # MAC
    key = RSA.import_key(priv_key)
    cipher = pkcs1_15.new(key)
    h = SHA256.new(data)
    mac = cipher.sign(h)

    # Encode for human readability
    ciphertext = b64encode(ciphertext).decode("utf-8")
    mac = b64encode(mac).decode("utf-8")

    return ciphertext, mac


def rsa_decrypt(ciphertext: bytes, mac: bytes, pub_key: str, priv_key: str) -> bytes:
    """ Decrypt via RSA """
    # Decode from base64
    ciphertext = b64decode(ciphertext)
    mac = b64decode(mac)

    # Plaintext
    # sentinel = Random.new().read(15+SHA256.digest_size)
    sentinel = None
    key = RSA.import_key(priv_key)
    cipher = PKCS1_v1_5.new(key)
    plaintext = cipher.decrypt(ciphertext, sentinel)

    # Verify
    key = RSA.import_key(pub_key)
    cipher = pkcs1_15.new(key)
    h = SHA256.new(plaintext)
    try:
        cipher.verify(h, mac)
        print("Signature verified!")
    except:
        print("Signature is not valid!")

    return plaintext
