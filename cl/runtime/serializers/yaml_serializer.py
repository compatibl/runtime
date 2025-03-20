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
from io import StringIO
from typing import Any
from uuid import UUID
from ruamel.yaml import YAML
from ruamel.yaml import StringIO
from ruamel.yaml.constructor import SafeConstructor
from ruamel.yaml.nodes import MappingNode
from ruamel.yaml.nodes import ScalarNode
from ruamel.yaml.nodes import SequenceNode
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.primitive_serializers import PrimitiveSerializers
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2

# Use primitive serializer with default settings to serialize all primitive types to string
primitive_to_string_serializer = PrimitiveSerializers.DEFAULT


def str_representer(dumper, data):
    """Configure YAML class for serializing a str field."""
    data_str = primitive_to_string_serializer.serialize(data, ["str | None"])
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=style)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def float_representer(dumper, data):
    """Configure YAML class for serializing a float field."""
    data_str = primitive_to_string_serializer.serialize(data, ["float | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:float", data_str, style=None)


def time_representer(dumper, data):
    """Configure YAML class for serializing a time field."""
    data_str = primitive_to_string_serializer.serialize(data, ["time | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:str", data_str)


def datetime_representer(dumper, data):
    """Configure YAML class for serializing a datetime field."""
    data_str = primitive_to_string_serializer.serialize(data, ["datetime | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data_str, style=None)


def uuid_representer(dumper, data):
    """Configure YAML class for serializing a UUID field."""
    data_str = primitive_to_string_serializer.serialize(data, ["UUID | None"])
    if data_str:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=None)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def bytes_representer(dumper, data):
    """Configure YAML class for serializing a bytes field."""
    data_str = primitive_to_string_serializer.serialize(data, ["bytes | None"])
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=style)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


# Roundtrip (typ=rt) style for the YAML writer is required to follow the formatting instructions in representers
yaml_writer = YAML(typ="rt")

# Add representers for writing the primitive types where YAML typ=rt format does not match our conventions
yaml_writer.representer.add_representer(str, str_representer)
yaml_writer.representer.add_representer(float, float_representer)
yaml_writer.representer.add_representer(dt.datetime, datetime_representer)
yaml_writer.representer.add_representer(dt.time, time_representer)
yaml_writer.representer.add_representer(UUID, uuid_representer)
yaml_writer.representer.add_representer(bytes, bytes_representer)


class PrimitiveToStringConstructor(SafeConstructor):
    """Custom constructor for YAML reader that ensures all primitive values are read as strings."""

    def construct_object(self, node, deep=False):
        """Convert from YAML types to native Python types."""
        if isinstance(node, ScalarNode):  # , ScalarString, ScalarFloat, ScalarInt)):  # Primitive types
            value = super().construct_scalar(node)
            if isinstance(value, (int, float, bool)):
                # Keep native Python types for int, float, bool
                return value
            else:
                # Convert everything except None to string, pass through None
                return str(value) if (value is not None and value != "") else None
        elif isinstance(node, SequenceNode):  # , CommentedSeq)):  # Lists
            return [self.construct_object(v, deep) for v in node.value]
        elif isinstance(node, MappingNode):  # , CommentedMap)):  # Dictionaries
            return {self.construct_object(k, deep): self.construct_object(v, deep) for k, v in node.value}
        return super().construct_object(node, deep)


# Override constructor in YAML reader for reading all types as strings
yaml_reader = YAML(typ="safe")
yaml_reader.Constructor = PrimitiveToStringConstructor


@dataclass(slots=True, kw_only=True)
class YamlSerializer(Freezable):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    bidirectional: bool | None = None
    """Use schema to validate and include _type in output to support both serialization and deserialization."""

    dict_serializer: DictSerializer2 | None = None
    """Serializes data into dictionary from which it is serialized into YAML."""

    dict_deserializer: DictSerializer2 | None = None
    """Deserializes the result of YAML parsing, including converting string leaf nodes to primitive types and enums."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.dict_serializer is None:
            # Create serializer and deserializer using the flags in this class
            # Serializer does serialize primitive types
            self.dict_serializer = DictSerializer2(
                pascalize_keys=self.pascalize_keys,
                bidirectional=self.bidirectional,
            ).build()
            # Deserializer uses default settings for deserializing primitive types from string
            self.dict_deserializer = DictSerializer2(
                pascalize_keys=self.pascalize_keys,
                bidirectional=self.bidirectional,
                primitive_serializer=PrimitiveSerializers.DEFAULT,
            ).build()
        else:
            # Check for mutually exclusive fields
            if self.pascalize_keys is not None:
                raise ErrorUtil.mutually_exclusive_fields_error(
                    ["pascalize_keys", "dict_serializer"],
                    class_name=TypeUtil.name(self),
                    details="When 'dict_serializer' field is set, its own 'pascalize_keys' setting will apply",
                )
            if self.bidirectional is not None:
                raise ErrorUtil.mutually_exclusive_fields_error(
                    ["bidirectional", "dict_serializer"],
                    class_name=TypeUtil.name(self),
                    details="When 'dict_serializer' field is set, its own 'bidirectional' setting will apply",
                )

    def serialize(self, data: Any) -> str:
        """
        Serialize a slots-based object to a YAML string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict
        data_dict = self.dict_serializer.serialize(data)

        # Use customized YAML object to follow the primitive type serialization conventions
        output = StringIO()
        yaml_writer.dump(data_dict, output)
        result = output.getvalue()
        return result

    def deserialize(self, serialized_data: str) -> Any:
        """Read a YAML string and return the deserialized object."""

        # Use customized YAML object to read all values as strings
        yaml_dict = yaml_reader.load(StringIO(serialized_data))

        # Convert to object using self.dict_serializer
        result = self.dict_deserializer.deserialize(yaml_dict)
        return result
