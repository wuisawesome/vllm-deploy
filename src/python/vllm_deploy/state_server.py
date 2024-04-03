from vllm_deploy.generated.state_pb2_grpc import RouterServiceServicer, add_RouterServiceServicer_to_server, WorkerService, add_WorkerServiceServicer_to_server
from vllm_deploy.generated import state_pb2
from vllm_deploy.logging import init_logging

import asyncio
import grpc
import logging

logger = logging.getLogger(__name__)


class Servicer(RouterServiceServicer, WorkerService):

    def __init__(self):
        self.worker_update = asyncio.Condition()
        self.workers = set()

    async def send_worker_reflection(self, context):
        logger.info(f"Writing updated workers to router! {self.workers=}")
        message = state_pb2.StateServerMessage(
            set_reflection=state_pb2.SetReflection(
                key="workers",
                new_set=list(self.workers)
            )
        )
        await context.write(message)


    async def RegisterRouter(self, request_iterator, context):
        """The channel between the router and state server.
        """

        async with self.worker_update:
            await self.send_worker_reflection(context)

        while True:
            async with self.worker_update:
                await self.worker_update.wait()
                await self.send_worker_reflection(context)


    async def handle_worker_heartbeat(self, heartbeat):
        async with self.worker_update:
            if heartbeat.worker_id not in self.workers:
                logger.info(f"Handling new worker heartbeat! {heartbeat}")
                self.workers.add(heartbeat.worker_id)
                self.worker_update.notify_all()


    async def remove_worker(self, last_heartbeat):
        async with self.worker_update:
            if last_heartbeat.worker_id in self.workers:
                logger.info(f"Removing worker {last_heartbeat}")
                self.workers.remove(last_heartbeat.worker_id)
                self.worker_update.notify_all()


    async def RegisterWorker(self, request_iterator, context):
        """When the stream ends, the worker should be automatically removed from the worker set.
        """
        last_heartbeat = None
        worker_event = await context.read()
        logger.info(f"A new worker is registering!")
        try:
            while True:
                if worker_event.HasField("heartbeat"):
                    last_heartbeat = worker_event.heartbeat
                    await self.handle_worker_heartbeat(worker_event.heartbeat)
                else:
                    assert False, f"Unknown worker service message {worker_event=}"

                # TODO: Timeout?
                worker_event = await context.read()
        except Exception as e:
            # Then again, there's no way for a worker to disconnect expectedly 🤔
            logger.info(f"Worker disconnected unexpectedly {e}")
        finally:
            if last_heartbeat is not None:
                await self.remove_worker(last_heartbeat)


_server = None
_servicer = None
async def get_or_create_grpc_server():
    global _server, servicer
    if _server is not None and _servicer is not None:
        return _server, _servicer

    port = "8080"
    _server = grpc.aio.server()
    _servicer = Servicer()

    add_RouterServiceServicer_to_server(_servicer, _server)
    add_WorkerServiceServicer_to_server(_servicer, _server)

    _server.add_insecure_port("[::]:" + port)
    logger.info("Starting server...")
    await _server.start()
    logger.info("Server started, listening on " + port)

    return _server, _servicer


async def main():
    _server, _ = await get_or_create_grpc_server()
    await _server.wait_for_termination()


if __name__ == "__main__":
    init_logging()
    asyncio.run(main())
