# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import vllm_deploy.generated.state_pb2 as state__pb2


class RouterServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterRouter = channel.stream_stream(
                '/RouterService/RegisterRouter',
                request_serializer=state__pb2.RouterServiceMessage.SerializeToString,
                response_deserializer=state__pb2.StateServerMessage.FromString,
                )


class RouterServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterRouter(self, request_iterator, context):
        """The channel between the router and state server.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RouterServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterRouter': grpc.stream_stream_rpc_method_handler(
                    servicer.RegisterRouter,
                    request_deserializer=state__pb2.RouterServiceMessage.FromString,
                    response_serializer=state__pb2.StateServerMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'RouterService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class RouterService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterRouter(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/RouterService/RegisterRouter',
            state__pb2.RouterServiceMessage.SerializeToString,
            state__pb2.StateServerMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class WorkerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterWorker = channel.stream_stream(
                '/WorkerService/RegisterWorker',
                request_serializer=state__pb2.WorkerServiceMessage.SerializeToString,
                response_deserializer=state__pb2.StateServerMessage.FromString,
                )


class WorkerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterWorker(self, request_iterator, context):
        """When the stream ends, the worker should be automatically removed from the worker set.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_WorkerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterWorker': grpc.stream_stream_rpc_method_handler(
                    servicer.RegisterWorker,
                    request_deserializer=state__pb2.WorkerServiceMessage.FromString,
                    response_serializer=state__pb2.StateServerMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'WorkerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class WorkerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterWorker(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/WorkerService/RegisterWorker',
            state__pb2.WorkerServiceMessage.SerializeToString,
            state__pb2.StateServerMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
