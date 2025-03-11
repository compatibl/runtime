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
from typing import Any
from uuid import UUID
from ruamel.yaml import YAML, StringIO
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2
from ruamel.yaml.nodes import ScalarNode, SequenceNode, MappingNode
from ruamel.yaml.constructor import SafeConstructor
from io import StringIO

# Serializer used by YAML representers to convert primitive types to YAML value string
representation_serializer = PrimitiveSerializer().build()

def float_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = representation_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:float', data_str, style=None)


def datetime_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = representation_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', data_str, style=None)


def time_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = representation_serializer.serialize(data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data_str)


def str_representer(dumper, data):
    """Use standard conversion to string for primitive types."""
    data_str = representation_serializer.serialize(data)
    style = "|" if data_str and "\n" in data_str else None
    return dumper.represent_scalar('tag:yaml.org,2002:str', data_str, style=style)

class StringOnlyConstructor(SafeConstructor):
    """Custom constructor for reading that ensures all values are read as strings."""

    def construct_object(self, node, deep=False):
        if isinstance(node, ScalarNode):  # Scalars (numbers, bools, strings)
            return str(super().construct_scalar(node))
        elif isinstance(node, SequenceNode):  # Lists
            return [self.construct_object(child, deep) for child in node.value]
        elif isinstance(node, MappingNode):  # Dictionaries
            return {str(self.construct_object(k, deep)): self.construct_object(v, deep) for k, v in node.value}
        return super().construct_object(node, deep)

# Use roundtrip style YAML to follow formatting instructions
yaml = YAML(typ='rt')

# Add representers for writing the primitive types where default format does not match our conventions
yaml.representer.add_representer(str, str_representer)
yaml.representer.add_representer(float, float_representer)
yaml.representer.add_representer(dt.datetime, datetime_representer)
yaml.representer.add_representer(dt.time, time_representer)
yaml.representer.add_representer(UUID, str_representer)
yaml.representer.add_representer(bytes, str_representer)

# Override constructor for reading all types as strings
yaml.Constructor = StringOnlyConstructor

@dataclass(slots=True, kw_only=True)
class YamlSerializer(Freezable):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _dict_serializer: DictSerializer2 = None
    """Serializes data into dictionary from which it is serialized into YAML."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self._dict_serializer = DictSerializer2(pascalize_keys=self.pascalize_keys).build()

    def to_yaml(self, data: Any) -> str:
        """
        Serialize a slots-based object to a YAML string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict with serialize_primitive flag set
        data_dict = self._dict_serializer.to_dict(data)

        # Use customized YAML object to follow the primitive type serialization conventions
        output = StringIO()
        yaml.dump(data_dict, output)
        result = output.getvalue()
        return result

    def from_yaml(self, serialized_data: str) -> Any:
        """Read a YAML string and return the deserialized object."""

        # Use customized YAML object to read all values as strings
        yaml_dict = yaml.load(StringIO(serialized_data))

        return yaml_dict
