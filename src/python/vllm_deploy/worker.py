import argparse
import asyncio
import grpc
import logging

from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm import SamplingParams

import vllm_deploy.generated.router_pb2 as router_pb2
import vllm_deploy.generated.router_pb2_grpc as router_pb2_grpc

logger = logging.getLogger(__name__)

def create_engine():
    parser = argparse.ArgumentParser(
            description='Demo on using the LLMEngine class directly'
    )
    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    engine_args = AsyncEngineArgs.from_cli_args(args)
    logging.info(f"Constructing engine from args {engine_args}")
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    return engine


async def infer_and_send_result(stub, engine, request_id):
    call = stub.ReportRequestResult()

    generator = engine.generate(
            "We the people of ",
            SamplingParams(),
            "request_id",
        )

    try:
        async for request_output in generator:
            assert len(request_output.outputs) == 1
            await call.write(
                router_pb2.CompletionChunk(
                    request_id=request_id,
                    choices=[
                        router_pb2.CompletionChunkChoice(
                            text=request_output.outputs[0].text
                        )
                    ]
                )
            )
    finally:
        # TODO: We should distinguish an error here.
        await call.done_writing()
        await call


async def main():
    parser = argparse.ArgumentParser(
                        prog='VLLM Deploy Worker',
                        description='Worker process',
        )
    parser.add_argument("--address", type=str, required=True)
    parser.add_argument("--bad", default=False, action='store_true')
    args = parser.parse_args()
    channel = grpc.aio.insecure_channel(args.address)

    stub = router_pb2_grpc.RouterServiceStub(channel)


    if args.bad:
        from vllm_deploy.really_bad_engine import ReallyBadEngine
        engine = ReallyBadEngine()
    else:
        engine = create_engine()

    await infer_and_send_result(stub, engine, "1")


asyncio.run(main())
