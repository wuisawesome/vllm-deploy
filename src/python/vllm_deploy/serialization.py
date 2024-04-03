import base64
import json
from typing import Any, Dict, List, Tuple, Union

_magic_footer = "**vllm=="


# Most of the code in this file was written/adapted from chatgpt.
class BytesEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, bytes):
            # Encode bytes to base64 and convert to string
            return base64.b64encode(obj).decode('ascii') + _magic_footer
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def dumps(obj) -> str:
    return json.dumps(obj, cls=BytesEncoder)


def _json_like_obj_hook(obj : Union[Dict[str, Any], List[Any], Any]) -> Any:
    if isinstance(obj, str) and obj.endswith(_magic_footer):
        to_decode = obj[:-len(_magic_footer)]
        decoded = base64.b64decode(to_decode.encode('ascii'))
        return decoded
    elif isinstance(obj, dict):
        return {
            key: _json_like_obj_hook(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [
            _json_like_obj_hook(item)
            for item in obj
        ]
    else:
        return obj



def loads(encoded_data : str) -> Any:
    return _json_like_obj_hook(json.loads(encoded_data))
