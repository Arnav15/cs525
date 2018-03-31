
class Blockchain(object):

    class BlockchainNode:
        def __init__(self, block_data=None, child_hash=None):
            self.data = block_data
            self.child_hash = child_hash


    def __init__(self):
        self._nodes = dict()
        self.head = None

    def add_block(self, new_block):
        block_hash = new_block.header.collation_id
        block_node = BlockchainNode(block_data=new_block)
        self._nodes[block_hash] = block_node

        # set the child of the current head, and change current head
        self._nodes[self.head].child_hash = block_hash
        self.head = block_hash

    def get_head(self):
        return self._nodes[self.head].data

    def verify_block(self):
        pass
