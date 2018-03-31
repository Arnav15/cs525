import argparse
import logging

import utils


class Client(object):

    RSA_KEY_FILE = 'rsakey.pem'

    def __init__(self, rsa_key_file=Client.RSA_KEY_FILE):
        self.rsa_key = utils.get_rsa_key(rsa_key_file)

        if self.rsa_key is None:
            self.rsa_key = utils.generate_rsa_key()
            utils.save_rsa_key(self.rsa_key)


def main(key_file=None):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser(description='AuntyMatter Client')

    parser.add_argument('--key-file',
        dest='key_file', default=None,
        help='The .pem key file for this Client')
    parser.add_argument('--log-file',
        dest='log_file', default='client.log',
        help='The file to write output log to')
    parser.add_argument('--log-level',
        dest='log_level', default='INFO', help='The log level',
        choices=['DEBUG', 'INFO', 'WARNING'])

    return args.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    log_level = getattr(logging, args.log_level)

    # setup logging
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        filename=args.log_file,
        filemode='w')

    main()
