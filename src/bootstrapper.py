import argparse
import asyncio
import sys

from p2p import BootstrapServerProtocol


def main(args):
    loop = asyncio.get_event_loop()
    nodes = set()

    coro = loop.create_server(
        lambda: BootstrapServerProtocol(nodes), host='0.0.0.0',
        port=BootstrapServerProtocol.BOOTSTRAP_NODE_PORT)
    loop.run_until_complete(coro)

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
    parser.add_argument('--log-file',
                        dest='log_file', default='/tmp/bootstrapper.log',
                        help='The file to write output log to')

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
