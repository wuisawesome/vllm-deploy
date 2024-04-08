from vllm_deploy.generated.state_pb2_grpc import RouterServiceStub
from vllm_deploy.generated.mailbox_pb2_grpc import MailboxServiceStub
from vllm_deploy.generated import state_pb2
from vllm_deploy.generated import mailbox_pb2
from vllm_deploy.logging import init_logging
from vllm_deploy.serialization import dumps, loads

import asyncio
from dataclasses import dataclass
import grpc
import logging
import random
import sys
from typing import Any, List, Dict, Optional, Callable, Awaitable
import uuid

logger = logging.getLogger(__name__)

@dataclass
class Workers:
    lock : asyncio.Lock
    workers : List[str]


async def schedule_scope(scope, workers : Workers):
    async with workers.lock:
        if len(workers.workers) == 0:
            return None
        return random.choice(workers.workers)

@dataclass
class Scope:
    scope_id : str
    worker_id : str
    scope_data : Dict[str, Any]
    finished : bool
    send_to_runner : Callable[[Dict[str, Any]], Awaitable]

class ScopeManager:
    def __init__(self, router_id):
        self.scopes_lock = asyncio.Lock()
        self.scopes = dict()
        self.router_id = router_id

        self.mailbox_host = "localhost"
        self.mailbox_port = 8081
        address = f"{self.mailbox_host}:{self.mailbox_port}"
        logger.info(f"Connecting to mailbox server on {address}")
        channel = grpc.aio.insecure_channel(address)
        self.mailbox_client = MailboxServiceStub(channel)

        self.mailbox_submission_lock = asyncio.Lock()
        self.mailbox_submisison_stream = None

        self.running = False

    async def start(self):
        self.mailbox_submission_stream = self.mailbox_client.SubmitMail()
        self.running = True
        self.mail_dispatcher_future = asyncio.create_task(self.mail_dispatcher_task())


    async def stop(self):
        self.running = False

    async def mail_dispatcher_task(self):
        logger.info("Mail dispatcher running")
        try:
            mailbox_subscription_call = self.mailbox_client.Subscribe(
                mailbox_pb2.SubscriptionRequest(
                    mailbox_id=self.router_id
                )
            )
            while self.running:
                mail = await mailbox_subscription_call.read()
                assert mail.HasField("new_event"), f"{mail=}"

                proto_event = mail.new_event

                scope_id = proto_event.scope_id
                asgi_event = loads(proto_event.payload)

                scope = None
                async with self.scopes_lock:
                    scope = self.scopes.get(scope_id)

                if scope is not None:
                    logger.info(f"Forward from worker {asgi_event}")
                    await scope.send_to_runner(asgi_event)
                else:
                    logger.warning(f"Scope {scope_id} wasn't found! Something bad probably happened.")
        except Exception:
            logger.exception("Mail dispatcher died! Shutting down.")
            await self.stop()


    async def handle_new_scope(self, worker, asgi_scope, receive, send):
        scope = Scope(
            scope_id=f"scope-{uuid.uuid4()}",
            worker_id=worker,
            scope_data=asgi_scope,
            send_to_runner=send,
            finished=False,
        )
        async with self.scopes_lock:
            self.scopes[scope.scope_id] = scope


        async with self.mailbox_submission_lock:
            logger.info(f"Forward scope {worker=} {scope=}")
            await self.mailbox_submission_stream.write(
                mailbox_pb2.MailMessage(
                    mailbox_id=worker,
                    new_scope=mailbox_pb2.NewAsgiScope(
                        scope_id=scope.scope_id,
                        router_id=self.router_id,
                        payload=dumps(asgi_scope),
                    )
                )
            )

        await self.forward_to_worker(worker, scope, receive)
        logger.info(f"Scope finished {scope=}")

    async def forward_to_worker(self, worker, scope, receive):
        while not scope.finished:
            event = await receive()

            logger.debug(f"Forward event to worker {worker=} {event=}")

            async with self.mailbox_submission_lock:
                await self.mailbox_submission_stream.write(
                    mailbox_pb2.MailMessage(
                        mailbox_id=worker,
                        new_event=mailbox_pb2.NewAsgiEvent(
                            scope_id=scope.scope_id,
                            payload=dumps(event).encode("utf-8")
                        )
                    )
                )
            # TODO: this doesn't feel great but serve does it 🤷‍♀️.
            # https://github.com/ray-project/ray/blob/fb89bf83385f66988e9df73364f7eeb277cfbebf/python/ray/serve/_private/http_util.py#L242-L242
            if event["type"] in {"http.disconnect", "websocket.disconnect"}:
                await self.end_scope(scope.scope_id)

    async def end_scope(self, scope_id):
        scope = None
        async with self.scopes_lock:
            scope = self.scopes.pop(scope_id)

        scope.finished = True


class RouterControlPlane:
    def __init__(self, router_id):
        self.router_id = router_id

        self._workers = Workers(
            lock=asyncio.Lock(),
            workers=set()
        )

        self.run_state_sync_loop = False

        self.router_service_host = "localhost"
        self.router_service_port = 8080
        address = f"{self.router_service_host}:{self.router_service_port}"
        logger.info(f"Connecting to state server on {address}")
        channel = grpc.aio.insecure_channel(address)
        self.router_service_client = RouterServiceStub(channel)

    async def start(self):
        self.run_state_sync_loop = True
        register_router_stream = self.router_service_client.RegisterRouter()
        asyncio.create_task(self.state_sync_loop(register_router_stream))

    async def stop(self):
        self.run_state_sync_loop = False

    async def handle_worker_set_reflection(self, update : state_pb2.SetReflection):
        assert update.key == "workers"
        async with self.workers.lock:
            self.workers.workers = list(update.new_set)
        logger.info(f"Update worker set to {update.new_set}")

    async def state_sync_loop(self, state_update_stream):
        try:
            while self.run_state_sync_loop:
                update = await state_update_stream.read()

                if update is None:
                    logger.error("Update shouldn't be none!")
                    next_update = await state_update_stream.read()
                    logger.error(f"GOt anotehr updte!!!")

                if update.HasField("set_reflection"):
                    await self.handle_worker_set_reflection(update.set_reflection)
                else:
                    logger.error(f"Got unknown state update {update=}")
        except Exception:
            logger.exception("Something went badly wrong")
            await self.stop()

    @property
    def workers(self):
        return self._workers


class ASGIApp:
    def __init__(self):
        self.router_id = f"router-{uuid.uuid4()}"
        self.router_control_plane = RouterControlPlane(self.router_id)
        self.scope_manager = ScopeManager(self.router_id)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self.handle_lifespan(scope, receive, send)
            return

        await self.handle_asgi_scope(scope, receive, send)


    async def handle_lifespan(self, scope, receive, send):
        message = await receive()
        assert message["type"] == "lifespan.startup"
        await self.start()
        await send({'type': 'lifespan.startup.complete'})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        await self.stop()

    async def start(self):
        await self.router_control_plane.start()
        await self.scope_manager.start()

    async def stop(self):
        await self.router_control_plane.stop()
        await self.scope_manager.stop()

    async def handle_asgi_scope(self, scope, receive, send):
        worker = await schedule_scope(scope, self.router_control_plane.workers)
        if worker is None:
            logger.error(f"Couldn't find a worker to schedule the scope on!")
        else:
            logger.info(f"Got scope, forwarding it to {worker=}")
            await self.scope_manager.handle_new_scope(worker, scope, receive, send)

init_logging()

# asgi app for the asgi runner to run.
app = ASGIApp()
