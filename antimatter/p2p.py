import asyncio
import pickle
import logging
import socket


class BootstrapServerProtocol(asyncio.Protocol):

    BOOTSTRAP_PORT = 8888

    def __init__(self, nodes):
        self.logger = logging.getLogger(BootstrapServerProtocol.__name__)
        self.nodes = nodes

    def connection_made(self, transport):
        ip = transport.get_extra_info('peername')[0]
        self.logger.info(f'Got connection from {ip}')
        transport.write(pickle.dumps(self.nodes))
        self.nodes.add(ip)
        transport.close()


class NetworkProtocol(asyncio.Protocol):

    DEFAULT_PORT = 9991

    def __init__(self, node_ref):
        self.logger = logging.getLogger(NetworkProtocol.__name__)
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


class NetworkClientProtocol(asyncio.Protocol):

    CLIENT_PORT = 9995

    def __init__(self, node_ref):
        self.logger = logging.getLogger(NetworkClientProtocol.__name__)
        self.node_ref = node_ref

    def connection_made(self, transport):
        self.ip = transport.get_extra_info('peername')[0]
        self.transport = transport
        self.node_ref.network.clients[self.ip] = transport
        self.logger.info(f'Got client connection from: {self.ip}')

    def connection_lost(self, exc):
        self.node_ref.network.clients[self.ip].close()
        del self.node_ref.network.clients[self.ip]
        self.logger.info(f'Client closed connection: {self.ip}')

    def data_received(self, data):
        self.logger.info(f'Received client msg from {self.ip}')
        try:
            message = pickle.loads(data)
        except pickle.UnpicklingError:
            self.logger.error('Message parsing error')

        self.node_ref.handle_message(message)

    def error_received(self, exc):
        pass


class Network:
    FQDN = 'antimatter-{}.anti-svc.antimatter-ns.svc.cluster.local'
    MAX_TRY_FAIL = 5

    def __init__(self, node_ref, evloop):
        self.logger = logging.getLogger(Network.__name__)
        # map peerhostname -> transport obj
        self.connections = dict()
        self.clients = dict()
        self.node_ref = node_ref
        self.evloop = evloop
        self.fqdn = socket.getfqdn()

    # async def get_membership_list(self):
    #     coro = asyncio.open_connection(
    #         Network.BOOTSTRAP_NODE_IP,
    #         Network.BOOTSTRAP_NODE_PORT, loop=self.evloop)
    #     reader, writer = await coro

    #     data = await reader.read()
    #     self.connections = dict.fromkeys(pickle.loads(data))
    #     self.logger.info(f'Received connections: {self.connections}')
    #     writer.close()

    async def create_connections(self, dst_port):
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
                transport, _ = await self.evloop.create_connection(
                    lambda: NetworkProtocol(self.node_ref),
                    host=node, port=dst_port)
                self.connections[node] = transport
            except OSError:
                self.logger.warn(f'Exception while connecting to {node}:')
                failed += 1

    async def create_endpoint(self, port):
        if port is None:
            port = NetworkProtocol.DEFAULT_PORT
        await self.evloop.create_server(
            lambda: NetworkProtocol(self.node_ref),
            host='0.0.0.0', port=port)

    async def create_client_endpoint(self, client_port):
        if client_port is None:
            client_port = NetworkClientProtocol.CLIENT_PORT
        await self.evloop.create_server(
            lambda: NetworkClientProtocol(self.node_ref),
            host='0.0.0.0', port=client_port)

    def broadcast_obj(self, obj):
        if not isinstance(obj, bytes) or not isinstance(obj, bytearray):
            pickled = obj.to_pickle()
        else:
            pickled = obj
        for peerhostname, transport in self.connections.items():
            self.logger.info(f'Sending to {peerhostname}')
            transport.write(pickled)

    def broadcast_obj_to_clients(self, obj):
        if not isinstance(obj, bytes) or not isinstance(obj, bytearray):
            pickled = obj.to_pickle()
        else:
            pickled = obj
        for peerhostname, transport in self.clients.items():
            self.logger.info(f'Sending to {peerhostname}')
            transport.write(pickled)
