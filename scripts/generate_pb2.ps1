# generate_pb2.ps1 — Regenerate all _pb2.py and _pb2_grpc.py files on Windows.
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
#   # From the repository root, using the Python on PATH:
#   .\scripts\generate_pb2.ps1
#
#   # Specify a Python interpreter explicitly:
#   .\scripts\generate_pb2.ps1 -Python C:\path\to\python.exe

param(
    # Path to the Python interpreter to use.  Defaults to 'python' on PATH.
    [string] $Python = "python"
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== Installing grpcio-tools 1.48.2 ===" -ForegroundColor Cyan
& $Python -m pip install "grpcio-tools==1.48.2" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed (exit code $LASTEXITCODE)."
    exit $LASTEXITCODE
}

Write-Host "=== Generating pb2 files ===" -ForegroundColor Cyan
Push-Location $repoRoot
try {
    $protoFiles = Get-ChildItem (Join-Path $repoRoot "ansys\api\edb\v1\*.proto") |
                  Select-Object -ExpandProperty FullName |
                  ForEach-Object { $_.Substring($repoRoot.Length + 1) -replace '\\', '/' }

    if (-not $protoFiles) {
        Write-Error "No .proto files found under ansys/api/edb/v1/."
        exit 1
    }

    & $Python -m grpc_tools.protoc `
        -I. `
        --python_out=. `
        --grpc_python_out=. `
        @protoFiles

    if ($LASTEXITCODE -ne 0) {
        Write-Error "protoc failed (exit code $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== Done - $($protoFiles.Count) proto files processed ===" -ForegroundColor Green
Write-Host "Review and commit the updated *_pb2.py and *_pb2_grpc.py files." -ForegroundColor Green
