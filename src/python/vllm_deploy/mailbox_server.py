from vllm_deploy.generated.mailbox_pb2_grpc import MailboxServiceServicer, add_MailboxServiceServicer_to_server
from vllm_deploy.generated import mailbox_pb2
from vllm_deploy.logging import init_logging

import asyncio
import grpc
import logging

init_logging()
logger = logging.getLogger(__name__)

class Servicer(MailboxServiceServicer):
    def __init__(self):
        self.lock = asyncio.Lock()
        self.mailboxes = dict()

    async def SubmitMail(self, request_iterator, context):
        """Stream to submit lots of mail.
        """
        try:
            async for mail in request_iterator:
                logger.info(f"Received new mail {mail=}")
                mailbox_id = mail.mailbox_id
                mailbox = None

                async with self.lock:
                    if mailbox_id not in self.mailboxes:
                        # TODO: There's definitely race conditions in worker
                        # registration here where a router could decide to forward
                        # requests to a mailbox before it has been set up. We
                        # should probably just set up the mailbox here, or at the
                        # very least let the sender know the message wasn't
                        # delivered.
                        logger.warning(f"{mailbox_id=} not found, perhaps the process recently died?")
                    else:
                        mailbox = self.mailboxes[mailbox_id]

                if mailbox is not None:
                    await mailbox.put(mail)
        except Exception:
            logger.info("Mail submission request finished, this likely means the client died.")

    async def Subscribe(self, request, context):
        """Stream of messages to a given mailbox.
        """
        logger.info(f"Got a subscriber! {request=}")
        mailbox = asyncio.Queue()
        async with self.lock:
            self.mailboxes[request.mailbox_id] = mailbox

        try:
            while True:
                mail = await mailbox.get()
                logger.info(f"Ready to forward mail. {mail=}")
                await context.write(mail)
        except Exception:
            logger.info(f"Subscriber died, this likely means the client died.")
        finally:
            async with self.lock:
                self.mailboxes.pop(request.mailbox_id)


_server = None
_servicer = None
async def get_or_create_grpc_server():
    global _server, servicer
    if _server is not None and _servicer is not None:
        return _server, _servicer

    port = "8081"
    _server = grpc.aio.server()
    _servicer = Servicer()

    add_MailboxServiceServicer_to_server(_servicer, _server)

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
