import asyncio
import logging
import pickle
import sys

from objects import *
import utils


class Proposer(object):

    def __init__(self):
        self.logger = logging.getLogger(Proposer.__name__)
        self.state = State()

    def handle_message(self, message):
        if isinstance(message, Transaction):
            return self.handle_transaction(message)

        self.logger.error('Received message cannot be handled by Proposer')

    def handle_transaction(self, txn):
        self.logger.info(f'Received transaction: {txn}')

        self.update_state(txn)

        # TODO: broadcast function

    def update_state(self, txn):
        # verify signature
        if not utils.verify_signature(
            self.src_pk, txn.serialize(), self.src_sig):
            self.logger.warn('Invalid signature')
            return

        total_input_value = 0.
        # verify src_pk owns inputs
        for coin_id in inputs:
            coin = self.state.remove_coin(coin_id)
            if coin.owner != txn.src_pk:
                return
            total_input_value += coin.value

        if total_input_value < txn.value:
            return

        leftover = total_input_value - txn.value

        if leftover > 0.:
            # mint a new coin (src_pk, leftover)
            coin = Coin(owner=txn.src_pk, value=leftover, parent_txn=txn.txn_id)
            self.state.add_coin(coin)

        # mint a new coin (dest_pk, total_input_value)
        coin = Coin(owner=txn.dest_pk, value=txn.value, parent_txn=txn.txn_id)
        self.state.add_coin(coin)


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
