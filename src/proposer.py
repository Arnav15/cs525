import asyncio
import logging
import pickle
import sys

from objects import *


class Proposer(object):

    def handle_message(message):
        if isinstance(message, Transaction):
            return handle_transaction(message)

        self.logger.error('Received message cannot be handled by Proposer')

    def handle_transaction(txn):
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
        BlockchainProtocol, local_addr=('127.0.0.1', 9999))
    loop.run_until_complete(udp_listener)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


if __name__ == '__main__':
    main()
