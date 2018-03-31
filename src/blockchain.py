class BlockchainNode:

    def __init__(self, block_data=None, parent_hash=None, children=list()):
        self.data = block_data
        self.parent_hash = parent_hash
        self.children = children


class Blockchain(object):

    def __init__(self):
        self.genesis_block = None
        self._nodes = dict()

    def add_block(self, new_block):
        block_hash = new_block.data.header.collation_id
        if self.genesis_block is None:
            self.genesis_block = block_hash
        else:
            parent_hash = new_block.data.header.parent_hash
            self._nodes[parent_hash].children.append(block_hash)
        self._nodes[block_hash] = new_block

    def verify_block(self):
        pass
