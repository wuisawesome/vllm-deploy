from vllm import SamplingParams
from vllm.outputs import RequestOutput, CompletionOutput

import asyncio
from typing import Optional, AsyncIterator


class ReallyBadEngine:

    # Match the relevant parts of the 
    async def generate(
        self,
        prompt: Optional[str],
        sampling_params: SamplingParams,
        request_id: str,
    ) -> AsyncIterator[RequestOutput]:
        to_yield = "a b c d e f".split(" ")

        text = ""
        for token in to_yield:
            text += token
            await asyncio.sleep(1)
            yield RequestOutput(
                request_id=request_id,
                prompt=prompt,
                prompt_token_ids=[],
                prompt_logprobs=[],
                outputs=[CompletionOutput(
                    index=0,
                    text=text,
                    token_ids=[],
                    cumulative_logprob=0.5,
                    logprobs=[],
                )],
                finished=False
            )


class ReallyBadServingChat:

    async def create_chat_completion(self):
        to_return = ["Lorem", "ipsum", "amit", "dolor", "[DONE]"]
        for token in to_return:
            yield token
