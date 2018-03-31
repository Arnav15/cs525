from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def generate_rsa_key():
    return = RSA.generate(2048)


def get_rsa_key(rsa_key_file):
    key = None
    if os.path.isfile(rsa_key_file):
        with open(rsa_key_file) as f:
            key = RSA.importKey(f.read())
    return key


def save_rsa_key(rsa_key, rsa_key_file):
    with open(rsa_key_file, 'w') as f:
        f.write(rsa_key.exportKey('PEM'))


def generate_signature(key, data):
    hashed = SHA256.new(data)
    signer = PKCS1_v1_5.new(key)
    return signer.sign(hashed)


def verify_signature(pk, data, sig):
    key = RSA.importKey(pk)
    hashed = SHA256.new(data)
    verifier = PKCS1_v1_5.new(key)
    return verifier.verify(hashed, sig)


def generate_hash(data):
    return SHA256.new(data).digest()


def merkle_root(items):
    pass
