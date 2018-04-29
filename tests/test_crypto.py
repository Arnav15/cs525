from antimatter.crypto import RSA, VRF


def test_vrf():
    priv_key1 = RSA.generate_rsa_key()
    priv_key2 = RSA.generate_rsa_key()

    vrf = VRF.compute_vrf(priv_key1, b'hello')

    assert vrf.verify(priv_key1.public_key(), b'hello')
    assert not vrf.verify(priv_key2.public_key(), b'hello')
    assert not vrf.verify(priv_key1.public_key(), b'hello-world')
