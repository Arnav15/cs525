from enum import Enum


class Role(Enum):
    PARTICIPANT = 0
    PROPOSER = 1
    COLLATOR = 2


class Shard(object):

    TOTAL_SHARDS = 3

    def __init__(self, shard_number=0):
        self.shard_number = shard_number
        self.role = Role.PARTICIPANT

    def generate_new(self, total_nodes):
        self.shard_number = randomrange(TOTAL_SHARDS)
        self.role = Role.PROPOSER

    def is_proposer(self):
        return self.role == Role.PROPOSER

    def is_collator(self):
        return self.role == Role.COLLATOR
