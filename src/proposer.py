import asyncio
import logging
import pickle
import sys

from copy import deepcopy

from objects import *
import utils


class Proposer(object):

    def __init__(self):
        self.logger = logging.getLogger(Proposer.__name__)
        self.state = State()
        self.transient_state = State()
        self.txn_pool = set()

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

        if self._update_state(txn):
            self.txn_pool.add(txn)
            self._broadcast_transaction(txn)

    def _update_state(self, txn):
        # verify signature
        if not utils.verify_signature(
                self.src_pk, txn.serialize(), self.src_sig):
            self.logger.warn('Invalid signature')
            return False

        total_input_value = 0.
        # verify src_pk owns inputs
        for coin_id in inputs:
            coin = self.transient_state.remove_coin(coin_id)
            if coin.owner != txn.src_pk:
                self.logger.warn('Coin not owned by sender')
                return False
            total_input_value += coin.value

        if total_input_value < txn.value:
            self.logger.warn('Not enough coins')
            return False

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


class BlockchainProtocol(asyncio.DatagramProtocol):

    def __init__(self):
        self.logger = logging.getLogger(BlockchainProtocol.__name__)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def datagram_received(self, data, addr):
        try:
            message = pickle.load(data)
        except pickle.UnpicklingError:
            self.logger.error('Message parsing error')

        Proposer.handle_message(message)

    def error_received(self, exc):
        pass


def main():
    loop = asyncio.get_event_loop()

    udp_listener = loop.create_datagram_endpoint(
        BlockchainProtocol, local_addr=('0.0.0.0', 9999))
    loop.run_until_complete(udp_listener)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


if __name__ == '__main__':
    main()
