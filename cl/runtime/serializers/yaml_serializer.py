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
from typing import Any, Type
from uuid import UUID
from ruamel.yaml import YAML, StringIO, CommentedMap, CommentedSeq
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import ScalarString

from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2
from ruamel.yaml.nodes import ScalarNode, SequenceNode, MappingNode
from ruamel.yaml.constructor import SafeConstructor
from io import StringIO

# Use primitive serializer with default settings to serialize all primitive types to string
primitive_to_string_serializer = PrimitiveSerializer().build()


def str_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = primitive_to_string_serializer.serialize(data)
    if data_str:
        style = "|" if data_str and "\n" in data_str else None
        return dumper.represent_scalar('tag:yaml.org,2002:str', data_str, style=style)
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:null', None, style=None)


def float_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = primitive_to_string_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:float', data_str, style=None)


def time_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = primitive_to_string_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data_str)


def datetime_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = primitive_to_string_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', data_str, style=None)

# Roundtrip (typ=rt) style for the YAML writer is required to follow the formatting instructions in representers
yaml_writer = YAML(typ='rt')

# Add representers for writing the primitive types where YAML typ=rt format does not match our conventions
yaml_writer.representer.add_representer(str, str_representer)
yaml_writer.representer.add_representer(float, float_representer)
yaml_writer.representer.add_representer(dt.datetime, datetime_representer)
yaml_writer.representer.add_representer(dt.time, time_representer)
yaml_writer.representer.add_representer(UUID, str_representer)
yaml_writer.representer.add_representer(bytes, str_representer)

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
                # Convert everything except None to string, passthrough None
                return str(value) if (value is not None and value != "") else None
        elif isinstance(node, SequenceNode):  # , CommentedSeq)):  # Lists
            return [self.construct_object(v, deep) for v in node.value]
        elif isinstance(node, MappingNode): # , CommentedMap)):  # Dictionaries
            return {
                self.construct_object(k, deep): self.construct_object(v, deep)
                for k, v in node.value
            }
        return super().construct_object(node, deep)

# Override constructor in YAML reader for reading all types as strings
yaml_reader = YAML(typ='safe')
yaml_reader.Constructor = PrimitiveToStringConstructor

@dataclass(slots=True, kw_only=True)
class YamlSerializer(Freezable):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    dict_serializer: DictSerializer2 = None
    """Serializes data into dictionary from which it is serialized into YAML."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self.dict_serializer = DictSerializer2(pascalize_keys=self.pascalize_keys).build()

    def to_yaml(self, data: Any) -> str:
        """
        Serialize a slots-based object to a YAML string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict
        data_dict = self.dict_serializer.to_dict(data)

        # Use customized YAML object to follow the primitive type serialization conventions
        output = StringIO()
        yaml_writer.dump(data_dict, output)
        result = output.getvalue()
        return result

    def from_yaml(self, serialized_data: str) -> Any:
        """Read a YAML string and return the deserialized object."""

        # Use customized YAML object to read all values as strings
        yaml_dict = yaml_reader.load(StringIO(serialized_data))

        # Convert to object using self.dict_serializer
        result = self.dict_serializer.from_dict(yaml_dict)
        return result
