"""Write out the rpc_response_map.py file."""
import re
from collections import defaultdict
from glob import iglob
from os import sep
from os.path import dirname, abspath
from typing import Dict, List, Tuple

from proto_parsing_utils import ProtoParserException, RpcData, parse_all_protos_in_dir

tab = "    "

_GOOGLE_WRAPPERS = {
    "BoolValue",
    "BytesValue",
    "DoubleValue",
    "FloatValue",
    "Int32Value",
    "Int64Value",
    "StringValue",
    "UInt32Value",
    "UInt64Value",
}
_GOOGLE_EMPTY = "Empty"
_GOOGLE_WRAPPERS_MODULE = "google.protobuf.wrappers_pb2"
_GOOGLE_EMPTY_MODULE = "google.protobuf.empty_pb2"


def _build_message_to_proto_map(protos_dir: str) -> Dict[str, str]:
    """Scan all proto files and return a map of message_name -> proto_file_name."""
    message_map = {}
    for proto_file in iglob(protos_dir + "/**/*.proto", recursive=True):
        proto_file_name = proto_file.split(sep)[-1].split(".")[0]
        with open(proto_file) as f:
            for line in f:
                match = re.match(r"^\s*message\s+(\w+)", line)
                if match:
                    msg_name = match.group(1)
                    if msg_name not in message_map:
                        message_map[msg_name] = proto_file_name
    return message_map


def _get_response_type_info(response_type: str, message_map: Dict[str, str]) -> Tuple[str, str]:
    """Return (short_class_name, python_module) for the given proto response type string."""
    if response_type.startswith("google.protobuf."):
        short_name = response_type.split(".")[-1]
        module = _GOOGLE_EMPTY_MODULE if short_name == _GOOGLE_EMPTY else _GOOGLE_WRAPPERS_MODULE
        return short_name, module
    proto_file_name = message_map.get(response_type)
    if proto_file_name is None:
        raise ProtoParserException(
            f"Could not find proto file for message type '{response_type}'."
        )
    return response_type, f"ansys.api.edb.v1.{proto_file_name}_pb2"


def _get_imports_str(rpc_datas: List[RpcData], message_map: Dict[str, str]) -> str:
    """Build all import statements for the response types used across all RPCs."""
    module_to_names = defaultdict(set)
    for rpc_data in rpc_datas:
        short_name, module = _get_response_type_info(rpc_data.response_type, message_map)
        module_to_names[module].add(short_name)

    import_lines = []
    for module in sorted(module_to_names):
        names = sorted(module_to_names[module])
        if len(names) == 1:
            import_lines.append(f"from {module} import {names[0]}")
        else:
            names_str = f",\n{tab}".join(names)
            import_lines.append(f"from {module} import (\n{tab}{names_str},\n)")

    return "\n".join(import_lines)


def _get_map_str(rpc_datas: List[RpcData], message_map: Dict[str, str]) -> str:
    """Build the body of the rpc_response_map dict."""
    service_to_rpcs = defaultdict(list)
    for rpc_data in rpc_datas:
        service_to_rpcs[rpc_data.full_service_name].append(rpc_data)

    service_entries = []
    for service_name in sorted(service_to_rpcs):
        rpc_entries = []
        for rpc_data in service_to_rpcs[service_name]:
            short_name, _ = _get_response_type_info(rpc_data.response_type, message_map)
            rpc_entries.append(f'{tab * 2}"{rpc_data.rpc_name}": {short_name}')
        rpcs_str = ",\n".join(rpc_entries)
        service_entries.append(f'{tab}"{service_name}": {{\n{rpcs_str},\n{tab}}}')

    return ",\n".join(service_entries)


def _get_rpc_response_map_file_str(rpc_datas: List[RpcData], message_map: Dict[str, str]) -> str:
    return f"""\"\"\"Defines map of RPC responses by service and method name.\"\"\"

{_get_imports_str(rpc_datas, message_map)}

rpc_response_map = {{
{_get_map_str(rpc_datas, message_map)}
}}


def get_rpc_response_type(service_name, rpc_name):
    \"\"\"Get the response type for the provided service and RPC names.\"\"\"
    service_map = rpc_response_map.get(service_name)
    return service_map.get(rpc_name) if service_map is not None else None
"""


def write_rpc_response_map_file(
    rpc_datas: List[RpcData], message_map: Dict[str, str], path: str
):
    with open(path, "w") as f:
        f.write(_get_rpc_response_map_file_str(rpc_datas, message_map))


if __name__ == "__main__":
    try:
        protos_dir = abspath(dirname(__file__) + "/../ansys/api/edb/v1")
        rpc_data = []
        parse_all_protos_in_dir(protos_dir, rpc_data, require_io_flags=False)
        message_map = _build_message_to_proto_map(protos_dir)
        output_path = abspath(dirname(__file__) + "/../ansys/api/edb/v1/rpc_response_map.py")
        write_rpc_response_map_file(rpc_data, message_map, output_path)
    except ProtoParserException as e:
        print(e)
