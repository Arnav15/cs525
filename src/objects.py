import abc
import pickle
import utils


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
        self.txn_id = utils.generate_hash(self.serialize())

    def __str__(self):
        return (f'src_pk={self.src_pk},dst_pk={self.dst_pk},'
                f'value={self.value},txn_id={self.txn_id}')

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        return ''.join([self.src_pk, self.dst_pk, self.value])


@BlockchainObject.register
class CollationHeader(BlockchainObject):

    def __init__(self, collation_id=None, shard_id=None, parent_hash=None,
                 txns_merkle_root=None, proposer_sig=None,
                 creation_timestamp=None):
        self.collation_id = collation_id
        self.shard_id = shard_id
        self.parent_hash = parent_hash
        self.txns_merkle_root = txns_merkle_root
        self.proposer_sig = proposer_sig
        self.creation_timestamp = creation_timestamp

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        pass


@BlockchainObject.register
class Collation(BlockchainObject):

    def __init__(self, header=None, transactions=list()):
        self.header = header
        self.transactions = transactions

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        pass


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
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        pass


@BlockchainObject.register
class Coin(BlockchainObject):

    def __init__(self, owner=None, value=None, parent_txn=None):
        self.owner = owner
        self.value = value
        self.parent_txn = parent_txn
        self.coin_id = utils.generate_hash(self.serialize())

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)

    def serialize(self):
        return ''.join([self.owner, self.value, self.parent_txn])
