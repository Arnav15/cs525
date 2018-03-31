from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def generate_signature(sk, data):
	key = RSA.importKey(sk)
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