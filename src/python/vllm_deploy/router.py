import vllm_deploy.generated.router_pb2 as router_pb2
import vllm_deploy.generated.router_pb2_grpc as router_pb2_grpc

from concurrent import futures
import grpc
import logging
import sys

logger = logging.getLogger(__name__)


def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


class RouterGrpcServicer(router_pb2_grpc.RouterServiceServicer):
    def __init__(self):
        pass

    def ReportRequestResult(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""

        logger.info("Received request")
        for chunk in request_iterator:
            assert len(chunk.choices) == 1
            text = chunk.choices[0].text
            logger.info(f"Chunk {text}")

        return router_pb2.Void()


if __name__ == "__main__":
    configure_logging()

    port = "8081"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    router_pb2_grpc.add_RouterServiceServicer_to_server(RouterGrpcServicer(), server)

    server.add_insecure_port("[::]:" + port)
    logger.info("Starting server...")
    server.start()
    logger.info("Server started, listening on " + port)
    server.wait_for_termination()

    print("Runnign main!!!!")

