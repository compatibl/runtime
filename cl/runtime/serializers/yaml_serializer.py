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

from frozendict import frozendict
from ruamel.yaml import YAML
from ruamel.yaml import StringIO
from ruamel.yaml.constructor import SafeConstructor
from ruamel.yaml.nodes import MappingNode
from ruamel.yaml.nodes import ScalarNode
from ruamel.yaml.nodes import SequenceNode
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.serializer import Serializer
from cl.runtime.serializers.type_hints import TypeHints

# TODO: Reuse YamlEncoder or avoid duplicated code in another way

# Use primitive serializer with default settings to serialize all primitive types to string
_PRIMITIVE_SERIALIZER = PrimitiveSerializers.DEFAULT


def str_representer(dumper, data):
    """Configure YAML class for serializing a str field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.STR_OR_NONE)
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=style)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def float_representer(dumper, data):
    """Configure YAML class for serializing a float field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.FLOAT_OR_NONE)
    return dumper.represent_scalar("tag:yaml.org,2002:float", data_str, style=None)


def time_representer(dumper, data):
    """Configure YAML class for serializing a time field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.TIME_OR_NONE)
    return dumper.represent_scalar("tag:yaml.org,2002:str", data_str)


def datetime_representer(dumper, data):
    """Configure YAML class for serializing a datetime field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.DATETIME_OR_NONE)
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data_str, style=None)


def uuid_representer(dumper, data):
    """Configure YAML class for serializing a UUID field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.UUID_OR_NONE)
    if data_str:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=None)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def bytes_representer(dumper, data):
    """Configure YAML class for serializing a bytes field."""
    data_str = _PRIMITIVE_SERIALIZER.serialize(data, TypeHints.BYTES_OR_NONE)
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar("tag:yaml.org,2002:str", data_str, style=style)
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:null", None, style=None)


def frozendict_representer(dumper, data):
    """Configure YAML class for serializing a frozendict field."""
    data_dict = {k:v for k, v in data.items()}
    return dumper.represent_mapping("tag:yaml.org,2002:map", data_dict)


# Roundtrip (typ=rt) style for the YAML writer is required to follow the formatting instructions in representers
yaml_writer = YAML(typ="rt")

# Add representers for writing the primitive types where YAML typ=rt format does not match our conventions
yaml_writer.representer.add_representer(str, str_representer)
yaml_writer.representer.add_representer(float, float_representer)
yaml_writer.representer.add_representer(dt.datetime, datetime_representer)
yaml_writer.representer.add_representer(dt.time, time_representer)
yaml_writer.representer.add_representer(UUID, uuid_representer)
yaml_writer.representer.add_representer(bytes, bytes_representer)
yaml_writer.representer.add_representer(frozendict, frozendict_representer)


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
class YamlSerializer(Serializer):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    data_serializer: Serializer = required()
    """Serializes data into dictionary from which it is serialized into YAML."""

    data_deserializer: Serializer | None = None
    """Deserializes the result of YAML parsing, including converting string leaf nodes to primitive types and enums."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize a slots-based object to a YAML string."""

        # Serialize to dict using self.dict_serializer
        serialized = self.data_serializer.serialize(data, type_hint)

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

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Read a YAML string and return the deserialized object if bidirectional flag is set, or dict otherwise."""

        if self.data_deserializer is None:
            raise RuntimeError("YAML data deserializer is not specified.")

        # Use a YAML reader with PrimitiveToStringConstructor to read all values as strings
        yaml_dict = yaml_reader.load(StringIO(data))

        # Deserialized from dict using self.dict_serializer
        result = self.data_deserializer.deserialize(yaml_dict, type_hint)
        return result
