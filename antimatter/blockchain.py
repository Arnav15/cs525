import random

from enum import Enum


class Role(Enum):
    PARTICIPANT = 0
    PROPOSER = 1
    COLLATOR = 2


class Blockchain(object):

    # hash is 32 byte string of 0's
    GENESIS_COLLATION_HASH = b'\x00' * 32

    class BlockchainNode:
        def __init__(self, block_data=None, child_hash=None):
            self.data = block_data
            self.child_hash = child_hash

    def __init__(self):
        self._nodes = dict()
        self.head = None

    def add_collation(self, new_collation):
        block_hash = new_collation.header.collation_id
        block_node = Blockchain.BlockchainNode(block_data=new_collation)
        self._nodes[block_hash] = block_node

        # set the child of the current head, and change current head
        self._nodes[self.head].child_hash = block_hash
        self.head = block_hash

    def get_head(self):
        return self._nodes[self.head].data

    def add_fork_node(self, new_collation):
        block_hash = new_collation.header.collation_id
        block_node = Blockchain.BlockchainNode(block_data=new_collation)
        self._nodes[block_hash] = block_node


class Shard(object):

    TOTAL_SHARDS = 3

    def __init__(self, shard_number=0):
        self.shard_number = shard_number
        self.role = Role.PARTICIPANT

    def generate_new(self, total_nodes):
        self.shard_number = random.randrange(Shard.TOTAL_SHARDS)
        self.role = Role.PROPOSER

    def is_proposer(self):
        return self.role == Role.PROPOSER

    def is_collator(self):
        return self.role == Role.COLLATOR
