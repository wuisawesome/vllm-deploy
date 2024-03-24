proto:
	mkdir -p src/python/vllm_deploy/generated/
	python -m grpc_tools.protoc -Isrc/proto --python_out=src/python/vllm_deploy/generated --grpc_python_out=src/python/vllm_deploy/generated src/proto/router.proto
	sed -i "" "s/import router_pb2/import vllm_deploy\.generated\.router_pb2/g" src/python/vllm_deploy/generated/router_pb2_grpc.py
