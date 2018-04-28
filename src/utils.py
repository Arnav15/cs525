import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def generate_rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )


def get_rsa_key(rsa_key_file):
    try:
        with open(rsa_key_file, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
            return private_key
    except:
        return None


def save_rsa_key(rsa_key, rsa_key_file):
    pem = rsa_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(rsa_key_file, 'wb') as f:
        f.write(pem)


def get_pub_key(private_key):
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def generate_signature(private_key, data):
    if not isinstance(data, bytes):
        data = bytes(data)

    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


def verify_signature(public_key, data, sig):
    if not isinstance(data, bytes):
        data = bytes(data)

    if not (isinstance(public_key, rsa.RSAPublicKey) or
            isinstance(public_key, rsa.RSAPublicKeyWithSerialization)):
        public_key = serialization.load_pem_public_key(
            public_key,
            backend=default_backend()
        )

    try:
        public_key.verify(
            sig,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature:
        return False
    return True


def generate_hash(data):
    if not isinstance(data, bytes):
        data = bytes(data)
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data)
    return digest.finalize()


def merkle_root(items):
    return
