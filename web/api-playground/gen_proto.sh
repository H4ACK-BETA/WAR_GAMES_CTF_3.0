#!/bin/bash
# Generate Python gRPC stubs from proto file
cd "$(dirname "$0")"
python -m grpc_tools.protoc \
    -I src/proto \
    --python_out=src/proto \
    --grpc_python_out=src/proto \
    src/proto/flag.proto

# Fix imports for package usage
sed -i 's/import flag_pb2/from . import flag_pb2/' src/proto/flag_pb2_grpc.py

echo "[+] Proto stubs generated"
