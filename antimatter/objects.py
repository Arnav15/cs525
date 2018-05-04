import abc
import pickle

from crypto import generate_hash, RSA


class BlockchainObject(abc.ABC):

    @abc.abstractmethod
    def to_pickle(self):
        pass

    @abc.abstractmethod
    def serialize(self):
        pass


@BlockchainObject.register
class Transaction(BlockchainObject):

    def __init__(self, src_pk=None, dst_pk=None, inputs=list(),
                 value=None, src_sig=None):
        self.src_pk = src_pk
        self.dst_pk = dst_pk
        self.inputs = inputs
        self.value = value
        self.src_sig = src_sig
        self.txn_id = generate_hash(self.serialize())

    def __str__(self):
        return (f'src_pk={self.src_pk},dst_pk={self.dst_pk},'
                f'inputs={self.inputs},value={self.value},'
                f'src_sig={self.src_sig},txn_id={self.txn_id}')

    def to_pickle(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        items = [self.src_pk, self.dst_pk, self.inputs, self.value]
        return bytearray(''.join(map(str, items)), encoding='UTF-8')

    def sign(self, priv_key):
        self.src_sig = RSA.generate_signature(priv_key, self.serialize())


@BlockchainObject.register
class CollationHeader(BlockchainObject):

    def __init__(self, shard_id=None, parent_hash=None,
                 txns_merkle_root=None, creation_timestamp=None,
                 proposer_sig=None):
        self.shard_id = shard_id
        self.parent_hash = parent_hash
        self.txns_merkle_root = txns_merkle_root
        self.creation_timestamp = creation_timestamp

        self.proposer_sig = proposer_sig
        self.collation_id = None

    def to_pickle(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        items = [self.shard_id, self.parent_hash, self.txns_merkle_root,
                 self.creation_timestamp]
        if self.proposer_sig is not None:
            items.append(self.proposer_sig)
        return bytearray(''.join(map(str, items)), encoding='UTF-8')


@BlockchainObject.register
class Collation(BlockchainObject):

    MAX_TXN_COUNT = 5

    def __init__(self, shard_id=None, parent_hash=None,
                 txns_merkle_root=None, creation_timestamp=None,
                 sign_callable=None, proposer_sig=None,
                 txns=list()):

        self.txns = txns
        if txns_merkle_root is None:
            # generate the merkle root
            # txns_merkle_root = merkle_root(txns)
            pass

        self.header = CollationHeader(
            shard_id=shard_id, parent_hash=parent_hash,
            txns_merkle_root=txns_merkle_root,
            creation_timestamp=creation_timestamp,
            proposer_sig=proposer_sig)

        # if no signature was provided, create it
        if proposer_sig is None:
            self.header.proposer_sig = sign_callable(self.serialize())

        # generate the collation hash (id)
        self.header.collation_id = generate_hash(self.serialize())

    def to_pickle(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        items = list()
        items.append(self.header.serialize())
        items.extend(map(lambda txn: txn.serialize(), self.txns))
        return bytearray(''.join(map(str, items)), encoding='UTF-8')


@BlockchainObject.register
class State(BlockchainObject):

    def __init__(self, utxo=dict()):
        self.utxo = utxo

    def add_coin(self, coin):
        self.utxo[coin.coin_id] = coin

    def get_coin(self, coin_id):
        return self.utxo.get(coin_id, None)

    def remove_coin(self, coin_id):
        return self.utxo.pop(coin_id)

    def to_pickle(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        pass


@BlockchainObject.register
class Coin(BlockchainObject):

    def __init__(self, owner=None, value=None, parent_txn=None):
        self.owner = owner
        self.value = value
        self.parent_txn = parent_txn
        self.coin_id = generate_hash(self.serialize())

    def to_pickle(self):
        pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        items = [self.owner, self.value, self.parent_txn]
        return bytearray(''.join(map(str, items)), encoding='UTF-8')


@BlockchainObject.register
class CollationVote(BlockchainObject):

    def __init__(self, collation_header, collator_pk, shard_number, proof,
                 sign_callable=None, collator_sig=None):
        self.header = collation_header
        self.collator_pk = collator_pk
        self.shard_number = shard_number
        self.proof = proof

        # if no signature was provided, create it
        if collator_sig is None:
            self.collator_sig = sign_callable(self.serialize())

    def to_pickle(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        items = [self.header.serialize(), self.collator_pk,
                 self.shard_number, self.proof]
        return bytearray(''.join(map(str, items)), encoding='UTF-8')
