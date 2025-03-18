"""Utility methods for parsing proto files."""

from glob import iglob
from os import linesep, sep
import re
from typing import List

import yaml


class ProtoParserException(Exception):
    """Exception class for handling issues when parsing proto files."""

    pass


valid_io_flags = {
    "buffer",
    "cache",
    "returns_future",
    "read_no_cache",
    "write_no_cache_invalidation",
}


class RpcData:
    """Container for rpc method properties."""

    def __init__(
        self,
        package_name: str,
        service_name: str,
        rpc_name: str,
        request_type: str,
        response_type: str,
        io_flags: List[str],
        proto_file_name: str,
    ):
        """Create an RpcData object."""
        self._package_name = package_name
        self._service_name = service_name
        self._rpc_name = rpc_name
        self._full_service_name = f"{self.package_name}.{self.service_name}"
        self._full_rpc_name = f"{self.full_service_name}.{self.rpc_name}"
        self._request_type = request_type
        self._response_type = response_type
        self._io_flags = set(io_flags)
        self._proto_file_name = proto_file_name

    @property
    def package_name(self):
        """Proto package name."""
        return self._package_name

    @property
    def service_name(self):
        """Service name."""
        return self._service_name

    @property
    def full_service_name(self):
        """Service name including package path."""
        return self._full_service_name

    @property
    def rpc_name(self):
        """Rpc method name."""
        return self._rpc_name

    @property
    def request_type(self):
        """Rpc method request type."""
        return self._request_type

    @property
    def response_type(self):
        """Rpc method response type."""
        return self._response_type

    @property
    def io_flags(self):
        """IO flags associated with the rpc method."""
        return self._io_flags

    @property
    def returns_future(self):
        """Flag indicating if the rpc method returns a future object."""
        return "returns_future" in self.io_flags

    @property
    def can_buffer(self):
        """Flag indicating if the rpc method call can be buffered."""
        return "buffer" in self.io_flags

    @property
    def full_rpc_name(self):
        """Full rpc method name including the package and service path."""
        return self._full_rpc_name

    def validate_io_flags(self):
        """Validate the parsed rpc method IO flags."""
        for io_flag in self.io_flags:
            if io_flag not in valid_io_flags:
                raise ProtoParserException(
                    f"encountered invalid io flag '{io_flag}' in rpc '{self.full_rpc_name}'"
                )

    @property
    def proto_file_name(self):
        """Name of the proto file defining the rpc method."""
        return self._proto_file_name


def _process_rpc(
    comments: List[str],
    rpc_decl: str,
    service_name: str,
    package_name: str,
    proto_file_name: str,
    rpc_datas: List[RpcData],
):
    rpc_info = yaml.safe_load(linesep.join([comment.replace("// ", "") for comment in comments]))
    if rpc_info is None or isinstance(rpc_info, str):
        return
    io_flags = rpc_info.get("io_flags")
    if io_flags is None or not io_flags:
        return
    rpc_method_tokens = [
        token for token in re.split(" |\(|\)", rpc_decl) if token and token != "stream"
    ]
    if len(rpc_method_tokens) != 6:
        raise ProtoParserException(
            f"Expected 6 delimited tokes but received {len(rpc_method_tokens)} in {rpc_decl}"
        )
    rpc_name = rpc_method_tokens[1]
    request = rpc_method_tokens[2]
    response = rpc_method_tokens[4]
    rpc_data = RpcData(
        package_name, service_name, rpc_name, request, response, io_flags, proto_file_name
    )
    rpc_data.validate_io_flags()
    rpc_datas.append(rpc_data)


def parse_proto(proto_path: str, rpc_datas: List[RpcData]):
    """Parse the provided proto file."""
    with open(proto_path) as proto_file:
        proto_datas = proto_file.readlines()

    proto_file_name = proto_path.split(sep)[-1].split(".")[-2]
    comments = []
    service = package = ""
    for proto_data in proto_datas:
        proto_data = proto_data.strip()
        if proto_data.startswith("//"):
            comments.append(proto_data)
            continue
        elif proto_data.startswith("rpc"):
            _process_rpc(comments, proto_data, service, package, proto_file_name, rpc_datas)
        elif proto_data.startswith("service"):
            service = proto_data.split()[1]
        elif proto_data.startswith("package"):
            package = proto_data.split()[-1][:-1]
        comments.clear()


def parse_all_protos_in_dir(protos_dir: str, rpc_datas: List[RpcData]):
    """Parse all proto files in the specified directory."""
    for proto_file in iglob(protos_dir + "/**/*.proto", recursive=True):
        parse_proto(proto_file, rpc_datas)
