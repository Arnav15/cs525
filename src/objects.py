import abc
import pickle


class BlockchainObject(abc.ABC):

    @abc.abstractmethod
    def to_pickle(self):
        pass


@BlockchainObject.register
class Transaction(BlockchainObject):

    def __init__(self, txn_id=None, src_pk=None, dst_pk=None, amount=None,
                 src_sig=None, creation_timestamp=None):
        self.txn_id = txn_id
        self.src_pk = src_pk
        self.dst_pk = dst_pk
        self.amount = amount
        self.src_sig = src_sig
        self.creation_timestamp = creation_timestamp

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)


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


@BlockchainObject.register
class Collation(BlockchainObject):

    def __init__(self, header=None, transactions=list()):
        self.header = header
        self.transactions = transactions

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)


@BlockchainObject.register
class State(BlockchainObject):

    def __init__(self, balances=dict()):
        self.balances = balances

    def update_balance(self, pk, amount):
        self.balances[pk] = amount

    def get_balance(self, pk):
        return self.balances.get(pk, 0)

    def to_pickle(self):
        pickle.dump(self, protocol=pickle.HIGHEST_PROTOCOL)
