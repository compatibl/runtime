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
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_format_enum import TypeFormatEnum
from cl.runtime.serializers.type_inclusion_enum import TypeInclusionEnum

# Use primitive serializer with default settings to serialize all primitive types to string
_PRIMITIVE_SERIALIZER = PrimitiveSerializers.DEFAULT


def str_representer(dumper, data):
    """Configure YAML class for serializing a str field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["str | None"])
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=style)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def float_representer(dumper, data):
    """Configure YAML class for serializing a float field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["float | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:float", data_str, style=None)


def time_representer(dumper, data):
    """Configure YAML class for serializing a time field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["time | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:str", data_str)


def datetime_representer(dumper, data):
    """Configure YAML class for serializing a datetime field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["datetime | None"])
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data_str, style=None)


def uuid_representer(dumper, data):
    """Configure YAML class for serializing a UUID field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["UUID | None"])
    if data_str:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=None)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def bytes_representer(dumper, data):
    """Configure YAML class for serializing a bytes field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, ["bytes | None"])
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
class YamlSerializer(Data):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    type_inclusion: TypeInclusionEnum = required()
    """Where to include type information in serialized data."""

    type_format: TypeFormatEnum | None = None
    """Format of the type information in serialized data (optional, do not provide if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _dict_serializer: DataSerializer = required()
    """Serializes data into dictionary from which it is serialized into YAML."""

    _dict_deserializer: DataSerializer | None = None
    """Deserializes the result of YAML parsing, including converting string leaf nodes to primitive types and enums."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Serializer passes through primitive types during serialization,
        # the conversions are done by the Ruamel YAML representers
        self._dict_serializer = DataSerializer(
            type_inclusion=self.type_inclusion,
            type_format=self.type_format,
            type_field=self.type_field,
            pascalize_keys=self.pascalize_keys,
            primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
            enum_serializer=EnumSerializers.DEFAULT,
        ).build()

        if self.type_format:
            # Create deserializer only if bidirectional flag is set
            # Deserializer uses default settings for deserializing primitive types from string
            self._dict_deserializer = DataSerializer(
                type_inclusion=self.type_inclusion,
                type_format=self.type_format,
                type_field=self.type_field,
                pascalize_keys=self.pascalize_keys,
                primitive_serializer=PrimitiveSerializers.DEFAULT,
                enum_serializer=EnumSerializers.DEFAULT,
            ).build()

    def serialize(self, data: Any) -> str:
        """
        Serialize a slots-based object to a YAML string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Serialize to dict using self.dict_serializer
        serialized = self._dict_serializer.serialize(data)

        if serialized is None:
            return ""
        elif serialized.__class__.__name__ in PRIMITIVE_CLASS_NAMES:
            # Use default primitive serializer for a primitive type
            result = PrimitiveSerializers.DEFAULT.serialize(serialized)
            # Add trailing newline
            return f"{result}\n"
        else:
            # Use a YAML writer with custom representers for any structured data
            output = StringIO()
            yaml_writer.dump(serialized, output)
            result = output.getvalue()
            return result

    def deserialize(self, yaml_str: str) -> Any:
        """Read a YAML string and return the deserialized object if bidirectional flag is set, and dict otherwise."""

        if self.type_inclusion == TypeInclusionEnum.OMIT:
            raise RuntimeError("Deserialization is not supported when type_inclusion=NEVER.")

        # Use a YAML reader with PrimitiveToStringConstructor to read all values as strings
        yaml_dict = yaml_reader.load(StringIO(yaml_str))

        # Deserialized from dict using self.dict_serializer
        result = self._dict_deserializer.deserialize(yaml_dict)
        return result
