import asyncio
import pickle
import logging


class BootstrapServerProtocol(asyncio.Protocol):

    BOOTSTRAP_NODE_IP = '126.2.2.2'
    BOOTSTRAP_NODE_PORT = 8888

    def __init__(self):
        self.nodes = list()

    def connection_made(self, transport):
        ip = transport.get_extra_info('peername')
        print(f'Got connection from {ip}')
        transport.write(pickle.dumps(self.nodes))
        self.nodes.append()
        transport.close()


class Network:

    class NetworkProtocol(asyncio.Protocol):
        def __init__(self, node):
            self.logger = logging.getLogger(Network.NetworkProtocol.__name__)
            self.node = node

        def connection_made(self, transport):
            ip = transport.get_extra_info('peername')
            self.node.network.connections[ip] = transport

        def connection_lost(self, exc):
            pass

        def data_received(self, data):
            try:
                message = pickle.load(data)
            except pickle.UnpicklingError:
                self.logger.error('Message parsing error')

            self.node.handle_message(message)

        def error_received(self, exc):
            pass

    DEFAULT_PORT = 9991

    BOOTSTRAP_NODE_IP = '126.2.2.2'
    BOOTSTRAP_NODE_PORT = 8888

    def __init__(self, node, evloop):
        self.connections = dict()
        self.node = node
        self.evloop = evloop

    async def get_membership_list(self):
        coro = asyncio.open_connection(
            Network.BOOTSTRAP_NODE_IP,
            Network.BOOTSTRAP_NODE_PORT, loop=self.evloop)
        reader, writer = await coro

        data = await reader.read()
        self.connections = dict.fromkeys(pickle.loads(data))
        writer.close()

    async def create_connections(self):
        new_connections = dict()
        for node in self.connections.keys():
            transport, protocol = await self.evloop.create_connection(
                lambda: Network.NetworkProtocol(self.node),
                host=node, port=Network.DEFAULT_PORT)
            new_connections[node] = transport
        self.connections.update(new_connections)

    async def create_endpoint(self, port=DEFAULT_PORT):
        await self.evloop.create_server(
            lambda: Network.NetworkProtocol(self.node),
            host='0.0.0.0', port=port)
