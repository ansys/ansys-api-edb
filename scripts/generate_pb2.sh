#!/usr/bin/env bash
# generate_pb2.sh — Regenerate all _pb2.py and _pb2_grpc.py files.
#
# The pb2 files are committed to the repository and packaged as-is by the
# normal build (setup.py no longer calls CMDCLASS_OVERRIDE, so 'python -m
# build' does NOT regenerate them automatically).
#
# Run this script manually when any .proto file changes, then commit the
# updated pb2 files alongside the proto changes.
#
# Requirements
# ------------
# grpcio-tools 1.48.2 bundles protobuf 3.19.6, which matches the version of
# libprotobuf bundled in AnsysEM (libprotobuf.so.3.19.6.0).  The generated
# pb2 files use the older protobuf 3 Python API, which is compatible with the
# 'protobuf>=3.19.3,<5' runtime constraint declared in setup.py.
#
# Using a newer grpcio-tools (e.g. 2.x / protobuf 5.x) produces pb2 files
# that require protobuf>=5 at runtime, which is incompatible with the
# AnsysEM-bundled libprotobuf.so.3.19.6.0 and will cause import errors.
#
# Usage
# -----
#   bash scripts/generate_pb2.sh            # uses Python on PATH
#   PYTHON=/path/to/python3 bash scripts/generate_pb2.sh

set -euo pipefail

PYTHON="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Installing grpcio-tools 1.48.2 ==="
"$PYTHON" -m pip install "grpcio-tools==1.48.2" --quiet

echo "=== Generating pb2 files ==="
cd "$REPO_ROOT"

PROTO_FILES=( ansys/api/edb/v1/*.proto )

"$PYTHON" -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    "${PROTO_FILES[@]}"

echo "=== Done — ${#PROTO_FILES[@]} proto files processed ==="
echo "Review and commit the updated *_pb2.py and *_pb2_grpc.py files."
