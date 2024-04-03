proto:
	rm -rf src/python/vllm_deploy/generated/
	mkdir -p src/python/vllm_deploy/generated/
	python -m grpc_tools.protoc -Isrc/proto --python_out=src/python/vllm_deploy/generated --grpc_python_out=src/python/vllm_deploy/generated src/proto/state.proto
	sed -i "" "s/import state_pb2/import vllm_deploy\.generated\.state_pb2/g" src/python/vllm_deploy/generated/state_pb2_grpc.py
	python -m grpc_tools.protoc -Isrc/proto --python_out=src/python/vllm_deploy/generated --grpc_python_out=src/python/vllm_deploy/generated src/proto/mailbox.proto
	sed -i "" "s/import mailbox_pb2/import vllm_deploy\.generated\.mailbox_pb2/g" src/python/vllm_deploy/generated/mailbox_pb2_grpc.py
