import argparse
import logging

import utils
import objects


class Client(object):

    RSA_KEY_FILE = 'rsakey.pem'

    def __init__(self, port=None, rsa_key_file=None):
        self.logger = logging.getLogger(Client.__name__)
        self.evloop = asyncio.get_event_loop()

        if rsa_key_file is None:
            rsa_key_file = Client.RSA_KEY_FILE

        self.state = State()
        self.txn_pool = list()
        self.blockchain = Blockchain()
        self.rsa_key = utils.get_rsa_key(rsa_key_file)

        if self.rsa_key is None:
            self.rsa_key = utils.generate_rsa_key()
            utils.save_rsa_key(self.rsa_key, rsa_key_file)

        # get and create connections
        self.network = Network(self, self.evloop)
        self.evloop.run_until_complete(self.network.get_membership_list())
        self.evloop.run_until_complete(self.network.create_connections())

    def send_message(self, message):
        while True:
            dst_pk, value = input().split(' ')

            # Create transaction
            args = {
                'src_pk': utils.get_pub_key(self.rsa_key),
                'dst_pk': dst_pk,
                'value': value
            }
            txn = Transaction(**args)
            txn.sign(self.rsa_key)

            # Send transaction
            self.network.broadcast_obj(txn)


def main(args):
    loop = asyncio.get_event_loop()

    client = Client(args.port, args.key_file)
    loop.create_task(client.send_message())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='AuntyMatter Client')

    parser.add_argument('-p', '--port',
                        dest='port', default=None,
                        help='Port to use to listen for incoming connections')
    parser.add_argument('--key-file',
                        dest='key_file', default=None,
                        help='The .pem key file for this Client')
    parser.add_argument('--log-file',
                        dest='log_file', default='client.log',
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
