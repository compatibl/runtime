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

from enum import Enum
from typing import Any
from frozendict import frozendict
from more_itertools import consume
from cl.runtime.records.protocols import MAPPING_CLASSES
from cl.runtime.records.protocols import SEQUENCE_CLASSES
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.protocols import is_empty
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.typename import typename


class FreezeUtil:
    """Helper methods for freezable and frozen data types."""

    @classmethod
    def freeze(cls, data: Any) -> Any:
        """
        Recursively convert sequence classes to tuples and mapping classes to frozendicts inside nested data
        and invoke freeze method for buildable classes without checking the type hint for public fields,
        pass through private and protected fields.
        """
        if is_empty(data):
            # Return None if data is None or an empty primitive type
            return None
        elif is_primitive(type(data)):
            # Pass through primitive types
            return data
        elif isinstance(data, Enum):
            # Pass through enums
            return data
        elif isinstance(data, SEQUENCE_CLASSES):
            # Convert all sequence types to tuple
            return tuple(cls.freeze(item) if not is_empty(item) else None for item in data)
        elif isinstance(data, MAPPING_CLASSES):
            # Convert all mapping types to frozendict
            return frozendict(
                (k, cls.freeze(v)) if not k.startswith("_") else v  # Do not freeze private or protected fields
                for k, v in data.items()
                if not is_empty(v)
            )
        elif is_data_key_or_record(data):
            if data.is_frozen():
                # Stop further processing and return if the object has already been frozen to
                # prevent repeat initialization of shared instances
                return data
            # Freeze public fields
            consume(
                setattr(data, k, cls.freeze(getattr(data, k))) for k in data.get_field_names() if not k.startswith("_")
            )
            return data.mark_frozen()
        else:
            raise RuntimeError(
                f"Cannot freeze data of type {typename(type(data))} because it is not\n"
                f"a primitive type, enum, data, key or record class,\n"
                f"or a supported container of these types."
            )
