import argparse
import asyncio
import glob
import logging
import random
import sys
import time

from blockchain import Blockchain
from crypto import RSA
from objects import State, Transaction
from p2p import Network, NetworkClientProtocol


class Client(object):

    TPS = 0.1

    def __init__(self, rsa_key_file=None):
        self.logger = logging.getLogger(Client.__name__)
        self.evloop = asyncio.get_event_loop()

        self.priv_key = None
        if rsa_key_file is not None:
            # use the supplied keyfile
            self.priv_key = RSA.get_rsa_key(rsa_key_file)

        # load the private key files
        self.keys = set()
        # read the client keys
        for key_file in glob.glob('client_keys/*.pem'):
            if key_file == rsa_key_file:
                continue
            self.keys.add(RSA.get_rsa_key(key_file))

        self.state = State()
        self.blockchain = Blockchain()

        # get and create connections
        self.network = Network(self, self.evloop)
        self.evloop.run_until_complete(
            self.network.create_connections(NetworkClientProtocol.CLIENT_PORT))

    def handle_message(self, message):
        if isinstance(message, Transaction):
            return self.handle_transaction(message)

        self.logger.error('Received message cannot be handled by Client')

    async def send_txns(self):
        while True:
            if self.priv_key is None:
                src_key, dst_key = random.sample(self.keys, 2)
            else:
                src_key = self.priv_key
                dst_key = random.sample(self.keys, 1)

            dst_key = dst_key.public_key()
            value = random.uniform(1., 10.)

            # Create transaction
            args = {
                'src_pk': RSA.get_pub_key_bytes(src_key),
                'dst_pk': RSA.get_pub_key_bytes(dst_key),
                'value': value,
                # 'inputs': ???
            }
            txn = Transaction(**args)
            txn.sign(src_key)
            self.logger.info(f'Created txn: {txn}')

            # Send transaction
            self.network.broadcast_obj(txn)

            # sleep until next transaction
            await asyncio.sleep(1 / Client.TPS)


def main(args):
    # add delay so that participants can bootstrap themselves
    time.sleep(10)

    loop = asyncio.get_event_loop()

    client = Client(args.key_file)
    loop.create_task(client.send_txns())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='AntiMatter Client')

    parser.add_argument('--key-file',
                        dest='key_file', default=None,
                        help='The .pem key file for this Client')
    parser.add_argument('--log-file',
                        dest='log_file', default='/tmp/client.log',
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
