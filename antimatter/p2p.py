import asyncio
import pickle
import logging
import socket


class BootstrapServerProtocol(asyncio.Protocol):

    BOOTSTRAP_NODE_PORT = 8888

    def __init__(self, nodes):
        self.logger = logging.getLogger(BootstrapServerProtocol.__name__)
        self.nodes = nodes

    def connection_made(self, transport):
        ip = transport.get_extra_info('peername')[0]
        self.logger.info(f'Got connection from {ip}')
        transport.write(pickle.dumps(self.nodes))
        self.nodes.add(ip)
        transport.close()


class Network:

    class NetworkProtocol(asyncio.Protocol):
        def __init__(self, node_ref):
            self.logger = logging.getLogger(Network.NetworkProtocol.__name__)
            self.node_ref = node_ref

        def connection_made(self, transport):
            self.ip = transport.get_extra_info('peername')[0]
            self.peerhostname = socket.gethostbyaddr(self.ip)[0]
            self.transport = transport
            self.node_ref.network.connections[self.peerhostname] = transport
            self.logger.info(f'Got connection from: {self.peerhostname}')

        def connection_lost(self, exc):
            self.node_ref.network.connections[self.peerhostname].close()
            del self.node_ref.network.connections[self.peerhostname]
            self.logger.info(f'LOST connection from: {self.peerhostname}')

        def data_received(self, data):
            self.logger.info(f'Received msg from {self.peerhostname}')
            try:
                message = pickle.loads(data)
            except pickle.UnpicklingError:
                self.logger.error('Message parsing error')

            self.node_ref.handle_message(message)

        def error_received(self, exc):
            pass

    DEFAULT_PORT = 9991
    FQDN = 'antimatter-{}.anti-svc.antimatter-ns.svc.cluster.local'
    MAX_TRY_FAIL = 5

    def __init__(self, node_ref, evloop):
        self.logger = logging.getLogger(Network.__name__)
        # map peerhostname -> transport obj
        self.connections = dict()
        self.node_ref = node_ref
        self.evloop = evloop
        self.fqdn = socket.getfqdn()

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
        node_id = 0
        failed = 0
        while failed < Network.MAX_TRY_FAIL:
            node = Network.FQDN.format(node_id)
            # increment node_id before loop logic kicks in
            node_id += 1

            if node == self.fqdn or node in self.connections:
                continue
            try:
                self.logger.info(f'Trying connect to {node}')
                transport, protocol = await self.evloop.create_connection(
                    lambda: Network.NetworkProtocol(self.node_ref),
                    host=node, port=Network.DEFAULT_PORT)
                self.connections[node] = transport
            except OSError:
                self.logger.warn(f'Exception while connecting to {node}:')
                failed += 1

    async def create_endpoint(self, port):
        if port is None:
            port = Network.DEFAULT_PORT
        await self.evloop.create_server(
            lambda: Network.NetworkProtocol(self.node_ref),
            host='0.0.0.0', port=port)

    def broadcast_obj(self, obj):
        if not isinstance(obj, bytes) or not isinstance(obj, bytearray):
            pickled = obj.to_pickle()
        else:
            pickled = obj
        for _, transport in self.connections.items():
            transport.write(pickled)
