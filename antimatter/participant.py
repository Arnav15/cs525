import argparse
import asyncio
import logging
import random
import sys

from copy import deepcopy
from datetime import datetime

from blockchain import Blockchain
from crypto import RSA
from objects import *
from p2p import Network
from shard import Shard


class Participant(object):

    RSA_KEY_FILE = 'rsakey.pem'

    def __init__(self, port=None, rsa_key_file=None):
        self.logger = logging.getLogger(Participant.__name__)
        self.evloop = asyncio.get_event_loop()

        if rsa_key_file is None:
            rsa_key_file = Participant.RSA_KEY_FILE

        self.state = State()
        self.txn_pool = dict()
        self.blockchain = Blockchain()
        self.rsa_key = RSA.get_rsa_key(rsa_key_file)

        if self.rsa_key is None:
            self.rsa_key = RSA.generate_rsa_key()
            RSA.save_rsa_key(self.rsa_key, rsa_key_file)

        # initialize epoch number and shard object
        self.epoch_number = 0
        self.shard = Shard()

        self.network = Network(self, self.evloop)

        # create TCP endpoint for incoming connections
        self.evloop.run_until_complete(self.network.create_endpoint(port))

        # start connecting to other nodes
        # self.evloop.run_until_complete(self.network.get_membership_list())
        self.evloop.run_until_complete(self.network.create_connections())

    def handle_message(self, message):
        if isinstance(message, Transaction):
            return self.handle_transaction(message)

        elif isinstance(message, Collation):
            return self.handle_collation(message)

        elif isinstance(message, CollationVote):
            return self.handle_collation_vote(message)

        self.logger.error('Received message cannot be handled by Proposer')

    def handle_transaction(self, txn):
        if txn.txn_id in self.txn_pool:
            self.logger.info(f'Received duplicate transaction: {txn}')
            return

        self.logger.info(f'Received transaction: {txn}')
        # verify signature
        if not RSA.verify_signature(
                txn.src_pk, txn.serialize(), txn.src_sig):
            self.logger.warn('Invalid signature')
            return False

        # transaction successfully added
        self.txn_pool[txn.txn_id] = txn
        self.network.broadcast_obj(txn)

    def _verify_txn_in_shard(self, src_pk):
        return int(bytes(src_pk)) % Shard.TOTAL_SHARDS == \
               self.shard.shard_number

    def _validate_txn(self, transient_state, txn):
        total_input_value = 0.
        coins_to_remove = list()
        # verify src_pk owns inputs
        for coin_id in txn.inputs:
            coin = transient_state.get_coin(coin_id)
            coins_to_remove.append(coin_id)
            if coin.owner != txn.src_pk:
                self.logger.warn('Coin not owned by sender')
                return False
            total_input_value += coin.value

        if total_input_value < txn.value:
            self.logger.warn('Not enough coins')
            return False

        # transaction verification complete, remove the coins
        self.logger.debug(f'Consuming coins: {coins_to_remove}')
        map(transient_state.remove_coin, coins_to_remove)

        leftover = total_input_value - txn.value
        if leftover > 0.:
            # mint a new coin (src_pk, leftover)
            coin = Coin(owner=txn.src_pk, value=leftover,
                        parent_txn=txn.txn_id)
            transient_state.add_coin(coin)

        # mint a new coin (dest_pk, total_input_value)
        coin = Coin(owner=txn.dest_pk, value=txn.value, parent_txn=txn.txn_id)
        transient_state.add_coin(coin)

        return True

    def _verify_collation(self, new_collation):
        # verify block hash

        # verify signature

        # verify txns merkle root

        # verify txns
        pass

    def handle_collation(self, collation):
        pass

    def handle_collation_vote(self, collation):
        pass

    async def create_collation(self):
        while True:
            # check if the node is a proposer
            if not self.shard.is_proposer:
                yield
                continue

            if len(self.txn_pool) < Collation.MAX_TXN_COUNT:
                yield
                continue

            def sign_callable(data):
                return RSA.generate_signature(self.rsa_key, data)

            txns = dict()
            num_txns = 0
            transient_state = deepcopy(self.state)
            while num_txns < Collation.MAX_TXN_COUNT and \
                    len(self.txn_pool) > 0:
                new_txn_id, new_txn = self.txn_pool.popitem()
                # verify new txn is valid and belongs to the proposer's shard
                if _verify_txn_in_shard(new_txn.src_pk) and \
                   _validate_txn(transient_state, new_txn):
                    txns[new_txn_id] = new_txn
                    num_txns += 1

            if num_txns < Collation.MAX_TXN_COUNT:
                self.txn_pool.update(txns)
                yield
                continue

            collation = Collation(
                shard_id=self.shard.shard_number,
                parent_hash=self.blockchain.get_head(),
                sign_callable=sign_callable,
                creation_timestamp=datetime.now().isoformat(),
                txns=txns.values())

            self.network.broadcast_obj(collation)
            yield


def main(args):
    loop = asyncio.get_event_loop()

    participant = Participant(args.port, args.key_file)
    loop.create_task(participant.create_collation())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='AntiMatter Participant')

    parser.add_argument('-p', '--port',
                        dest='port', default=None,
                        help='Port to use to listen for incoming connections')
    parser.add_argument('--key-file',
                        dest='key_file', default=None,
                        help='The .pem key file for this Participant')
    parser.add_argument('--log-file',
                        dest='log_file', default='/tmp/participant.log',
                        help='The file to write output log to')
    parser.add_argument('--log-level',
                        dest='log_level', default='INFO', help='The log level',
                        choices=['DEBUG', 'INFO', 'WARNING'])

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    log_level = getattr(logging, args.log_level)

    # setup logging
    fh = logging.FileHandler(args.log_file, mode='w')
    sh = logging.StreamHandler()
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        handlers=[fh, sh])

    main(args)
