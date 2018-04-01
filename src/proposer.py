import argparse
import asyncio
import logging
import sys

from copy import deepcopy
from datetime import datetime

from blockchain import Blockchain
from discovery import Network
from objects import *
import utils


class Proposer(object):

    RSA_KEY_FILE = 'rsakey.pem'

    def __init__(self, port=None, rsa_key_file=Proposer.RSA_KEY_FILE):
        self.logger = logging.getLogger(Proposer.__name__)
        self.evloop = asyncio.get_event_loop()

        self.state = State()
        self.transient_state = State()
        self.txn_pool = set()
        self.blockchain = Blockchain()
        self.rsa_key = utils.get_rsa_key(rsa_key_file)

        if self.rsa_key is None:
            self.rsa_key = utils.generate_rsa_key()
            utils.save_rsa_key(self.rsa_key)

        # get and create connections
        self.network = Network(self, self.evloop)
        self.evloop.run_until_complete(self.network.get_membership_list())
        self.evloop.run_until_complete(self.network.create_connections())
        # create TCP endpoint for incoming connections
        self.evloop.run_until_complete(self.network.create_endpoint(port))

    def handle_message(self, message):
        if isinstance(message, Transaction):
            return self.handle_transaction(message)

        elif isinstance(message, Collation):
            return self.handle_collation(message)

        self.logger.error('Received message cannot be handled by Proposer')

    def handle_transaction(self, txn):
        self.logger.info(f'Received transaction: {txn}')

        if self.transient_state.is_stale:
            self.transient_state = deepcopy(self.state)

        if self._update_transient_state(txn):
            # transaction successfully added
            self.txn_pool.add(txn)
            self._broadcast_transaction(txn)

    def _update_transient_state(self, txn):
        # verify signature
        if not utils.verify_signature(
                txn.src_pk, txn.serialize(), txn.src_sig):
            self.logger.warn('Invalid signature')
            return False

        total_input_value = 0.
        coins_to_remove = list()
        # verify src_pk owns inputs
        for coin_id in inputs:
            coin = self.transient_state.get_coin(coin_id)
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
        map(self.transient_state.remove_coin, coins_to_remove)

        leftover = total_input_value - txn.value
        if leftover > 0.:
            # mint a new coin (src_pk, leftover)
            coin = Coin(owner=txn.src_pk, value=leftover,
                        parent_txn=txn.txn_id)
            self.transient_state.add_coin(coin)

        # mint a new coin (dest_pk, total_input_value)
        coin = Coin(owner=txn.dest_pk, value=txn.value, parent_txn=txn.txn_id)
        self.transient_state.add_coin(coin)

        return True

    def _broadcast_transaction(self, txn):
        # TODO: broadcast function
        pass

    def handle_collation(self, collation):
        pass

    def _broadcast_collation(self, collation):
        # TODO: broadcast function
        pass

    async def create_collation(self):
        while True:
            if len(self.txn_pool) < Collation.MAX_TXN_COUNT:
                yield
                continue

            def sign_callable(data):
                return utils.generate_signature(self.rsa_key, data)

            transactions = list()
            for _ in range(Collation.MAX_TXN_COUNT):
                transactions.append(self.txn_pool.pop())

            collation = Collation(
                shard_id=0,
                parent_hash=self.blockchain.get_head(),
                sign_callable=sign_callable,
                creation_timestamp=datetime.now().isoformat(),
                transactions=transactions)

            # add this collation to the chain
            self.blockchain.add_block(collation)

            yield


def main(args):
    loop = asyncio.get_event_loop()

    proposer = Proposer(args.port, args.key_file)
    loop.create_task(proposer.create_collation())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='AuntyMatter Proposer')

    parser.add_argument('-p', '--port',
                        dest='port', default=None,
                        help='Port to use to listen for incoming connections')
    parser.add_argument('--key-file',
                        dest='key_file', default=None,
                        help='The .pem key file for this Proposer')
    parser.add_argument('--log-file',
                        dest='log_file', default='proposer.log',
                        help='The file to write output log to')
    parser.add_argument('--log-level',
                        dest='log_level', default='INFO', help='The log level',
                        choices=['DEBUG', 'INFO', 'WARNING'])

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    log_level = getattr(logging, args.log_level)

    # setup logging
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        filename=args.log_file,
        filemode='w')

    main(args)
