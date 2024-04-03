from vllm_deploy.generated.state_pb2_grpc import WorkerServiceStub
from vllm_deploy.generated.mailbox_pb2_grpc import MailboxServiceStub
from vllm_deploy.generated import state_pb2
from vllm_deploy.generated import mailbox_pb2
from vllm_deploy.logging import init_logging
from vllm_deploy.serialization import dumps, loads
from vllm_deploy.importer import import_from_string

import asyncio
from dataclasses import dataclass
import grpc
import logging
import random
import sys
import time
from typing import Any, Dict, List
import uuid

logger = logging.getLogger(__name__)

@dataclass
class Scope:
    scope_id : str
    router_id : str
    data : Dict[str, Any]
    received_events : asyncio.Queue


class ScopeManager:
    def __init__(self):
        self.scopes_lock = asyncio.Lock()
        self.scopes = dict()

    async def handle_new_scope(self, scope_proto : mailbox_pb2.NewAsgiScope) -> Scope:
        scope_id = scope_proto.scope_id
        logger.info(f"Handling new scope {scope_proto=}")
        scope = Scope(
            scope_id=scope_proto.scope_id,
            router_id=scope_proto.router_id,
            data=loads(scope_proto.payload),
            received_events=asyncio.Queue()
        )
        async with self.scopes_lock:
            self.scopes[scope_id] = scope

        return scope

    async def remove_scope(self, scope_id : str):
        async with self.scopes_lock:
            self.scopes.pop(scope_id)

    async def handle_new_event(self, event_proto : mailbox_pb2.NewAsgiEvent):
        scope_id = event_proto.scope_id
        event = loads(event_proto.payload)

        scope = None
        # This locking might not be necessary?
        async with self.scopes_lock:
            scope = self.scopes.get(scope_id)

        if scope is not None:
            await scope.received_events.put(event)


class WorkerGrpcClient:
    def __init__(self, state_server_address, mailbox_server_address, scope_handler, event_handler):
        self.scope_handler = scope_handler
        self.event_handler = event_handler
        self.worker_id = f"worker-{uuid.uuid4()}"

        self.should_stop = False

        # self.worker_service_host = "localhost"
        # self.worker_service_port = 8080
        # address = f"{self.worker_service_host}:{self.worker_service_port}"
        logger.info(f"Connecting to state server on {state_server_address}")
        channel = grpc.aio.insecure_channel(state_server_address)
        self.worker_service_client = WorkerServiceStub(channel)

        # self.mailbox_host = "localhost"
        # self.mailbox_port = 8081
        # mailbox_server_address = f"{self.mailbox_host}:{self.mailbox_port}"
        logger.info(f"Connecting to mailbox server on {mailbox_server_address}")
        channel = grpc.aio.insecure_channel(mailbox_server_address)
        self.mailbox_client = MailboxServiceStub(channel)
        self.mailbox_send_stream = None

    async def stop(self):
        self.should_stop = True

    async def send_mail(self, message : mailbox_pb2.MailMessage):
        logger.debug(f"Sending mail! {message=}")
        await self.mailbox_send_stream.write(message)

    async def start_request_processing(self):
        try:
            mailbox_subscription_call = self.mailbox_client.Subscribe(
                mailbox_pb2.SubscriptionRequest(
                    mailbox_id=self.worker_id,
                )
            )
            self.mailbox_send_stream = self.mailbox_client.SubmitMail()
            logger.info(f"Starting event processing...")
            while not self.should_stop:
                mail = await mailbox_subscription_call.read()
                logger.info(f"Got mail! {mail=}")

                if mail.HasField("new_scope"):
                    await self.scope_handler(mail.new_scope)
                elif mail.HasField("new_event"):
                    await self.event_handler(mail.new_event)
                else:
                    logger.error(f"Got unknown type of mail {mail=}")

        except Exception:
            logger.exception("Fatal exception, stopping")
        finally:
            await self.stop()

    async def send_heartbeats(self):
        try:
            call_context = self.worker_service_client.RegisterWorker()
            while not self.should_stop:
                heartbeat = state_pb2.WorkerServiceMessage(
                    heartbeat=state_pb2.WorkerHeartbeat(
                        worker_id=self.worker_id
                    )
                )
                logger.debug(f"Sending heartbeat {int(time.time())}")
                await call_context.write(heartbeat)

                await asyncio.sleep(5)
        except Exception:
            logger.exception("Fatal exception, stopping")
        finally:
            await self.stop()

    async def start_control_plane_connection(self):
        asyncio.create_task(self.send_heartbeats())


    async def wait_until_completion(self):
        while not self.should_stop:
            await asyncio.sleep(1)


class AsgiRunner:
    def __init__(self, app, state_server_address, mailbox_server_address):
        self.app = app
        self.scope_manager = ScopeManager()
        self.grpc_client = WorkerGrpcClient(state_server_address, mailbox_server_address, self.handle_new_scope, self.handle_new_event)

    async def start(self):
        logger.info(f"Spawning event processing loop")
        asyncio.create_task(self.grpc_client.start_request_processing())
        logger.info(f"Spawning control plane loop")
        asyncio.create_task(self.grpc_client.start_control_plane_connection())

    async def stop(self):
        await self.grpc_client.stop()

    async def wait_until_completion(self):
        await self.grpc_client.wait_until_completion()

    async def new_scope_task(self, scope : Scope):
        receive = scope.received_events.get

        async def send(asgi_event):
            logger.debug(f"Sending asgi event {asgi_event=}")
            await self.grpc_client.send_mail(
                mailbox_pb2.MailMessage(
                    mailbox_id=scope.router_id,
                    new_event=mailbox_pb2.NewAsgiEvent(
                        scope_id=scope.scope_id,
                        payload=dumps(asgi_event)
                    )
                )
            )

        await self.app(scope.data, receive, send)
        await self.scope_manager.remove_scope(scope.scope_id)

    async def handle_new_scope(self, scope_proto : mailbox_pb2.NewAsgiScope):
        scope = await self.scope_manager.handle_new_scope(scope_proto)
        asyncio.create_task(self.new_scope_task(scope))

    async def handle_new_event(self, event_proto : mailbox_pb2.NewAsgiEvent):
        await self.scope_manager.handle_new_event(event_proto)


async def app(scope, receive, send):
    request = await receive()
    logger.info(f"WOOOOHOOOOO app received request {request=}")
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            [b"content-type", b"text/plain"],
        ],
    })
    await send({
        "type": "http.response.body",
        "body": b"Hello, World!",
    })


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("app")
    parser.add_argument("--state-server-address", default="localhost:8080")
    parser.add_argument("--mailbox-server-address", default="localhost:8081")
    args = parser.parse_args()

    app = import_from_string(args.app)
    runner = AsgiRunner(app, args.state_server_address, args.mailbox_server_address)
    await runner.start()
    await runner.wait_until_completion()

if __name__ == "__main__":
    init_logging()
    asyncio.run(main())
