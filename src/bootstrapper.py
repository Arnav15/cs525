import argparse
import asyncio
import sys

from discovery import BootstrapServerProtocol


def main(args):
    loop = asyncio.get_event_loop()

    loop.create_server(BootstrapServerProtocol, host='0.0.0.0',
                       port=BootstrapServerProtocol.BOOTSTRAP_NODE_PORT)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Quitting...', file=sys.stderr)

    loop.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='AuntyMatter Bootstrapper')

    parser.add_argument('-p', '--port',
                        dest='port', default=None,
                        help='Port to use to listen for incoming connections')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    main(args)
