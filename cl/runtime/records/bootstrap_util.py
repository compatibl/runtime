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
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.typename import typename


class BootstrapUtil:
    """Helper methods for build functionality in BootstrapMixin."""

    @classmethod
    def build(cls, data: Any) -> Any:
        """
        The implementation of the build method in BootstrapUtil performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Calls its 'mark_frozen' method without performing validation against the schema
        """
        if data is None:
            # Pass through None
            return data
        elif (data_class_name := typename(data)) in PRIMITIVE_CLASS_NAMES:
            # Pass through primitive types
            return data
        elif is_enum(data):
            # Pass through enum types
            return data
        elif data_class_name in SEQUENCE_TYPE_NAMES:
            # Convert a sequence types to tuple after applying build to each item
            return tuple(cls.build(v) for v in data)
        elif data_class_name in MAPPING_TYPE_NAMES:
            # Convert a mapping type to frozendict after applying build to each item
            return frozendict((k, cls.build(v)) for k, v in data.items())
        elif is_data_key_or_record(data):
            # Has slots, process as data, key or record
            if data.is_frozen():
                # Pass through if already frozen to prevent repeat initialization of shared instances
                return data

            # Invoke '__init' in the order from base to derived
            # Keep track of which init methods in class hierarchy were already called
            invoked = set()
            # Reverse the MRO to start from base to derived
            for class_ in reversed(type(data).__mro__):
                # Remove leading underscores from the class name when generating mangling for __init
                # to support classes that start from _ to mark them as protected
                class_init = getattr(class_, f"_{class_.__name__.lstrip('_')}__init", None)
                if class_init is not None and (qualname := class_init.__qualname__) not in invoked:
                    # Add qualname to invoked to prevent executing the same method twice
                    invoked.add(qualname)
                    # Invoke '__init' method if it exists, otherwise do nothing
                    class_init(data)

            # Apply updates to the data object
            tuple(
                setattr(data, k, cls.build(v))
                for k in data.get_field_names()
                if (
                    # Exclude those types that are passed through
                    (v := getattr(data, k)) is not None
                    and type(v).__name__ not in PRIMITIVE_CLASS_NAMES
                    and not isinstance(v, Enum)
                    # Exclude protected and private fields
                    and not k.startswith("_")
                )
            )

            # Mark as frozen to prevent further modifications
            return data.mark_frozen()
        else:
            raise cls._unsupported_object_error(data)

    @classmethod
    def _unsupported_object_error(cls, obj: Any) -> Exception:
        obj_type_name = typename(obj)
        return RuntimeError(
            f"Class {obj_type_name} cannot be a record or its field. Supported types include:\n"
            f"  1. Classes that implement 'build' method;\n"
            f"  2. Sequence types (list, tuple, etc.) where all values are supported types;\n"
            f"  3. Mapping types (dict, frozendict, etc.) with string keys where all values are supported types;\n"
            f"  4. Enums; and\n5. Primitive types from the following list:\n{', '.join(PRIMITIVE_CLASS_NAMES)}"
        )
