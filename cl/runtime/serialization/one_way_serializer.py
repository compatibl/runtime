# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime as dt
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any
from uuid import UUID

import orjson
import yaml
from frozendict import frozendict
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.format_util import FormatUtil
from cl.runtime.serialization.slots_util import SlotsUtil
from cl.runtime.records.protocols import _PRIMITIVE_TYPE_NAMES


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


class MultiLineStringDumper(yaml.SafeDumper):
    """Custom dumper to use block style for multi-line strings."""
    def represent_scalar(self, tag, value, style=None):
        """Use block style (|) for multiline strings."""
        if isinstance(value, str) and "\n" in value:
            style = "|"
        return super().represent_scalar(tag, value, style)


def float_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = FormatUtil.format(data)
    return dumper.represent_scalar('tag:yaml.org,2002:float', data_str, style=None)


def datetime_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = FormatUtil.format(data)
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', data_str, style=None)


def str_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = FormatUtil.format(data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data_str, style=None)


def enum_representer(dumper, data):
    """Use standard conversion to string for enums."""
    item_name = CaseUtil.upper_to_pascal_case(data.name)  # Use FormatUtil
    return dumper.represent_scalar('tag:yaml.org,2002:str', item_name, style=None)


# Add primitive type representers to MultiLineStringDumper for
# those types where YAML default output format does not match
# the primitive type serialization in FormatUtil.
yaml.add_representer(float, float_representer, Dumper=MultiLineStringDumper)
yaml.add_representer(dt.datetime, datetime_representer, Dumper=MultiLineStringDumper)
yaml.add_representer(dt.time, str_representer, Dumper=MultiLineStringDumper)
yaml.add_representer(UUID, str_representer, Dumper=MultiLineStringDumper)
yaml.add_representer(bytes, str_representer, Dumper=MultiLineStringDumper)

# Add enum representer to MultiLineStringDumper
yaml.add_multi_representer(Enum, enum_representer, Dumper=MultiLineStringDumper)


@dataclass(slots=True, kw_only=True)
class OneWaySerializer:
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    def to_json(self, data: Any) -> str:
        """
        Serialize a slots-based object to a JSON string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict with serialize_primitive flag set
        data_dict = self.to_dict(data, serialize_primitive=True)

        # Use orjson to serialize the dictionary to JSON in pretty-print format
        result = orjson.dumps(data_dict, option=orjson.OPT_INDENT_2).decode()
        return result

    def to_yaml(self, data: Any) -> str:
        """
        Serialize a slots-based object to a YAML string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict with serialize_primitive flag set
        data_dict = self.to_dict(data) # , serialize_primitive=True)

        # Use pyyaml with custom dumper to serialize the dictionary to YAML in pretty-print format
        result = yaml.dump(
            data_dict,
            default_style=None,
            default_flow_style=False,
            sort_keys=False,
            Dumper=MultiLineStringDumper,
        )
        return result

    def to_dict(self, data: Any, *, serialize_primitive: bool | None = None) -> Any:
        """
        Serialize a slots-based object to a dictionary without using the schema or retaining type information,
        not suitable for deserialization.

        Args:
            data: Data to serialize
            serialize_primitive: Convert primitive types to strings during serialization if set
        """

        if getattr(data, "__slots__", None) is not None:
            # Get slots from this class and its bases in the order of declaration from base to derived
            all_slots = SlotsUtil.get_slots(data.__class__)
            # Serialize slot values in the order of declaration except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (FormatUtil.format(v) if serialize_primitive else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else v.name if isinstance(v, Enum)
                    else self.to_dict(v, serialize_primitive=serialize_primitive)
                )
                for k in all_slots
                if (v := getattr(data, k)) is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        elif isinstance(data, list) or isinstance(data, tuple):
            # Assume that type of the first item is the same as for the rest of the collection
            is_primitive_collection = len(data) > 0 and data[0].__class__.__name__ in _PRIMITIVE_TYPE_NAMES
            if is_primitive_collection:
                # More efficient implementation for a primitive collection
                if serialize_primitive:
                    return [
                        "None" if v is None
                        else FormatUtil.format(v)
                        for v in data
                    ]
                else:
                    return data
            else:
                # Not a primitive collection, serialize complex elements or enums
                result = [
                    "None" if serialize_primitive else None if v is None
                    else (FormatUtil.format(v) if serialize_primitive else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else v.name if isinstance(v, Enum)
                    else self.to_dict(v, serialize_primitive=serialize_primitive)
                    for v in data
                ]
            return result
        elif isinstance(data, dict) or isinstance(data, frozendict):
            # Dictionary, return with serialized values except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (FormatUtil.format(v) if serialize_primitive else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else v.name if isinstance(v, Enum)
                    else self.to_dict(v, serialize_primitive=serialize_primitive)
                )
                for k, v in data.items()
                if v is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")
