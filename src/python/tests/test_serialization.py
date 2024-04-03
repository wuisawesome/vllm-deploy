from vllm_deploy.serialization import dumps, loads


def test_empty():
    event = {'type': 'http.request', 'body': b'', 'more_body': False}
    assert event == loads(dumps(event))

def test_basic():
    event = {'type': 'http.request', 'body': b'hello', 'more_body': False}
    assert event == loads(dumps(event))

def test_embedded():
    event={'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'text/plain']]}
    assert event == loads(dumps(event))
