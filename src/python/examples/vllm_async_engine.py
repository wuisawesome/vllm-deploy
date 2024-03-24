import argparse

from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs

from vllm import SamplingParams

parser = argparse.ArgumentParser(
        description='Demo on using the LLMEngine class directly'
)
parser = AsyncEngineArgs.add_cli_args(parser)
args = parser.parse_args()

engine_args = AsyncEngineArgs.from_cli_args(args)
print(f"Engine args {engine_args}")


engine = AsyncLLMEngine.from_engine_args(engine_args)

async def run(engine):
    generator = engine.generate(
            "We the people of ",
            SamplingParams(),
            "request_id",
        )

    async for request_output in generator:
        print(request_output.outputs)


import asyncio
asyncio.run(run(engine))

"""
python example.py --model mistralai/Mistral-7B-v0.1

INFO 03-24 00:41:26 async_llm_engine.py:436] Received request request_id: prompt: 'We the people of ', prefix_pos: None,sampling_params: SamplingParams(n=1, best_of=1, presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0, temperature=1.0, top_p=1.0, top_k=-1, min_p=0.0, seed=None, use_beam_search=False, length_penalty=1.0, early_stopping=False, stop=[], stop_token_ids=[], include_stop_str_in_output=False, ignore_eos=False, max_tokens=16, logprobs=None, prompt_logprobs=None, skip_special_tokens=True, spaces_between_special_tokens=True), prompt_token_ids: None, lora_request: None.
[CompletionOutput(index=0, text=' the', token_ids=[272], cumulative_logprob=-2.0577845573425293, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth', token_ids=[272, 6340], cumulative_logprob=-8.013906002044678, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n', token_ids=[272, 6340, 13], cumulative_logprob=-11.037644386291504, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\n', token_ids=[272, 6340, 13, 13], cumulative_logprob=-11.396291494369507, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\nded', token_ids=[272, 6340, 13, 13, 3802], cumulative_logprob=-18.62095046043396, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated', token_ids=[272, 6340, 13, 13, 3802, 6899], cumulative_logprob=-19.552741646766663, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\n', token_ids=[272, 6340, 13, 13, 3802, 6899, 13], cumulative_logprob=-22.86390745639801, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532], cumulative_logprob=-26.222847819328308, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272], cumulative_logprob=-26.93520313501358, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201], cumulative_logprob=-28.722977936267853, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354], cumulative_logprob=-37.61837035417557, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for one', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354, 624], cumulative_logprob=-42.086048901081085, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for one people', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354, 624, 905], cumulative_logprob=-45.02685981988907, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for one people one', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354, 624, 905, 624], cumulative_logprob=-47.581251204013824, logprobs=None, finish_reason=None)]
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for one people one law', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354, 624, 905, 624, 2309], cumulative_logprob=-52.317772924900055, logprobs=None, finish_reason=None)]
INFO 03-24 00:41:27 async_llm_engine.py:110] Finished request request_id.
[CompletionOutput(index=0, text=' the earth\n\ndedicated\nto the proposition for one people one law\n', token_ids=[272, 6340, 13, 13, 3802, 6899, 13, 532, 272, 26201, 354, 624, 905, 624, 2309, 13], cumulative_logprob=-53.27407932281494, logprobs=None, finish_reason=length)]
root@d72d7fbf26c3:/workspace# 

"""
