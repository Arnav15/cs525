import asyncio
import pickle
import logging


class BootstrapServerProtocol(asyncio.Protocol):

    BOOTSTRAP_NODE_PORT = 8888

    def __init__(self, nodes):
        self.nodes = nodes

    def connection_made(self, transport):
        ip = transport.get_extra_info('peername')[0]
        self.logger.info(f'Got connection from {ip}')
        transport.write(pickle.dumps(self.nodes))
        self.nodes.add(ip)
        transport.close()


class Network:

    class NetworkProtocol(asyncio.Protocol):
        def __init__(self, node):
            self.logger = logging.getLogger(Network.NetworkProtocol.__name__)
            self.node = node

        def connection_made(self, transport):
            ip = transport.get_extra_info('peername')[0]
            self.transport = transport
            self.ip = ip
            self.node.network.connections[ip] = transport
            self.logger.info(f'Got connection from: {self.ip}')

        def connection_lost(self, exc):
            self.node.network.connections[self.ip].close()
            del self.node.network.connections[self.ip]
            self.logger.info(f'LOST connection from: {self.ip}')

        def data_received(self, data):
            try:
                message = pickle.load(data)
            except pickle.UnpicklingError:
                self.logger.error('Message parsing error')

            self.node.handle_message(message)

        def error_received(self, exc):
            pass

    DEFAULT_PORT = 9991

    BOOTSTRAP_NODE_IP = 'sp18-cs525-g05-01.cs.illinois.edu'
    BOOTSTRAP_NODE_PORT = 8888

    def __init__(self, node, evloop):
        self.logger = logging.getLogger(Network.__name__)
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
        self.logger.info(f'Received connections: {self.connections}')
        writer.close()

    async def create_connections(self):
        new_connections = dict()
        for node in self.connections.keys():
            try:
                transport, protocol = await self.evloop.create_connection(
                    lambda: Network.NetworkProtocol(self.node),
                    host=node, port=Network.DEFAULT_PORT)
                new_connections[node] = transport
            except ConnectionRefusedError:
                self.logger.warn(f'Could not connect to {node}')
        self.connections.update(new_connections)

    async def create_endpoint(self, port):
        if port is None:
            port = Network.DEFAULT_PORT
        await self.evloop.create_server(
            lambda: Network.NetworkProtocol(self.node),
            host='0.0.0.0', port=port)

    def broadcast_obj(self, obj):
        if not isinstance(obj, bytes) or not isinstance(obj, bytearray):
            pickled = obj.to_pickle()
        else:
            pickled = obj
        for ip, transport in self.connections.iteritems():
            transport.write(pickled)
