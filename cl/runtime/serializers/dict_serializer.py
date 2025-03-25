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
from enum import Enum
from typing import Any
from typing import Dict
from typing import Type
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.records.protocols import TDataField
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.record_util import RecordUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.annotations_util import AnnotationsUtil
from cl.runtime.serializers.sentinel_type import sentinel_value
from cl.runtime.serializers.slots_util import SlotsUtil

# TODO: Initialize from settings
_type_dict: Dict[str, Type] | None = None
"""Dictionary of types using class name or alias as key (includes all classes and enums)."""


# TODO: Move to a separate helper class
def get_type_dict() -> Dict[str, Type]:
    """Load type dictionary from schema if not present."""
    global _type_dict
    if _type_dict is None:
        from cl.runtime.schema.schema import Schema  # TODO: Refactor to avoid cyclic dependency

        _type_dict = Schema.get_type_dict()

    return _type_dict


# TODO: Add checks for to_node, from_node implementation for custom override of default serializer
@dataclass(slots=True, kw_only=True)
class DictSerializer:
    """Serialization for slots-based classes (including dataclasses with slots=True)."""

    pascalize_keys: bool = False
    """If true, pascalize keys during serialization."""

    primitive_type_names = {
        "NoneType",
        "str",
        "float",
        "bool",
        "bytes",
        "UUID",
    }
    """Detect primitive type by checking if class name is in this list."""

    def serialize_data(
        self, data: TRecord, annot_type: Type | None = None
    ) -> dict[str, Any]:  # TODO: Check if None should be supported
        """
        Serialize to dictionary containing primitive types, dictionaries, or iterables.

        Args:
            data: Object to serialize
            annot_type: Annotation type
        """

        annot_type = AnnotationsUtil.handle_optional_annot(annot_type)
        if getattr(data, "__slots__", None) is not None:
            # Slots class, serialize as dictionary
            # Get slots from this class and its bases in the order of declaration from base to derived
            data_type = type(data)
            all_slots = SlotsUtil.get_slots(data_type)
            annots = AnnotationsUtil.get_class_hierarchy_annotations(data_type)
            # Serialize slot values in the order of declaration except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case_keep_trailing_underscore(k)): (
                    v
                    if (v_annot := annots.get(k)) is not Any and v.__class__.__name__ in self.primitive_type_names
                    else self.serialize_data(v, v_annot)
                )
                for k in all_slots
                if (v := getattr(data, k)) is not None
            }
            # To find short name, use 'in' which is faster than 'get' when most types do not have aliases
            short_name = TypeUtil.name(data_type)
            # Cache type for subsequent reverse lookup
            type_dict = get_type_dict()
            type_dict[short_name] = data_type
            # Add to result
            result["_type"] = short_name
            return result
        elif data.__class__.__name__ == "date":
            return dt.datetime.combine(data, dt.datetime.min.time()).replace(tzinfo=dt.timezone.utc)
        elif data.__class__.__name__ == "time":
            return TimeUtil.to_iso_int(TimeUtil.round(data))
        elif data.__class__.__name__ == "datetime":
            return DatetimeUtil.round(data)
        # 'int' is not a primitive because it could be dt.time on deserialization
        elif data.__class__.__name__ in self.primitive_type_names or data.__class__.__name__ == "int":
            return data
        elif isinstance(data, dict):
            dict_value_annot_type = AnnotationsUtil.extract_dict_value_annot_type(annot_type)
            # Dictionary, return with serialized values
            result = {
                k: (
                    v
                    if v.__class__.__name__ in self.primitive_type_names and dict_value_annot_type is not Any
                    else self.serialize_data(v, dict_value_annot_type)
                )
                for k, v in data.items()
            }
            return result
        elif hasattr(data, "__iter__"):
            # Get the first item without iterating over the entire sequence
            first_item = next(iter(data), sentinel_value)

            # Get origin type and its args
            _, iter_value_annot_type = AnnotationsUtil.extract_iterable_origin_and_args(annot_type)

            if first_item == sentinel_value:
                # Empty iterable, return None
                return None
            elif (
                first_item is not None
                and first_item.__class__.__name__ in self.primitive_type_names
                and iter_value_annot_type is not Any
            ):
                # Performance optimization to skip deserialization for arrays of primitive types
                # based on the type of first item (assumes that all remaining items are also primitive)
                return data
            else:
                # Serialize each element of the iterable
                return [  # type: ignore
                    (
                        v
                        if iter_value_annot_type is not Any and v.__class__.__name__ in self.primitive_type_names
                        else self.serialize_data(v, iter_value_annot_type)
                    )
                    for v in data
                ]
        elif isinstance(data, Enum):
            # Serialize enum as a dict using enum class short name and item name (rather than item value)
            # To find short name, use 'in' which is faster than 'get' when most types do not have aliases
            enum_type = data.__class__
            short_name = TypeUtil.name(enum_type)
            # Cache type for subsequent reverse lookup
            type_dict = get_type_dict()
            type_dict[short_name] = enum_type
            pascal_case_value = CaseUtil.upper_to_pascal_case(data.name)
            return {"_enum": short_name, "_name": pascal_case_value}
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def deserialize_data(self, data: TDataField, type_: Type | None = None):  # TODO: Check if None should be supported
        """
        Deserialize object from data, invoke init_all after deserialization.

        The optional "annot_type" parameter will be passed recursively for fields that aren't primitives and aren't
        serialized dataclasses. For a serialized dataclasses, the type is specified in the "_type" attribute.
        """

        # Extract inner type if type_ is Optional[...]
        type_ = AnnotationsUtil.handle_optional_annot(type_)

        if isinstance(data, dict):
            # Determine if the dictionary is a serialized dataclass or a dictionary
            if (short_name := data.get("_type", None)) is not None:
                # If _type is specified, create an instance of _type after deserializing fields recursively
                type_dict = get_type_dict()
                deserialized_type = type_dict.get(short_name, None)  # noqa
                if deserialized_type is None:
                    raise RuntimeError(
                        f"Class not found for name or alias '{short_name}' during deserialization. "
                        f"Ensure all serialized classes are included in package import settings."
                    )

                # Check if the class is abstract
                if RecordUtil.is_abstract(deserialized_type):
                    descendants = RecordUtil.get_non_abstract_descendants(deserialized_type)
                    descendant_names = sorted(set([x.__name__ for x in descendants]))
                    if len(descendant_names) > 0:
                        descendant_names_str = ", ".join(descendant_names)
                        raise UserError(
                            f"Record {deserialized_type.__name__} cannot be created directly, "
                            f"but the following descendant records can: {descendant_names_str}"
                        )
                    else:
                        raise UserError(
                            f"Record {deserialized_type.__name__} cannot be created directly "
                            f"and there are no descendant records that can."
                        )

                annots = AnnotationsUtil.get_class_hierarchy_annotations(deserialized_type)
                deserialized_fields = {
                    (CaseUtil.pascale_to_snake_case_keep_trailing_underscore(k) if self.pascalize_keys else k): (
                        v
                        if v.__class__.__name__ in self.primitive_type_names
                        else self.deserialize_data(
                            v,
                            annots.get(
                                CaseUtil.pascale_to_snake_case_keep_trailing_underscore(k) if self.pascalize_keys else k
                            ),
                        )
                    )
                    for k, v in data.items()
                    if k != "_type" and not k.startswith("_")
                }
                result = deserialized_type(**deserialized_fields)  # noqa
                return result
            elif (short_name := data.get("_enum", None)) is not None:
                # If _enum is specified, create an instance of _enum using _name
                type_dict = get_type_dict()
                deserialized_type = type_dict.get(short_name, None)  # noqa
                if deserialized_type is None:
                    raise RuntimeError(
                        f"Enum not found for name or alias '{short_name}' during deserialization. "
                        f"Ensure all serialized enums are included in package import settings."
                    )
                pascal_case_value = data["_name"]
                upper_case_value = CaseUtil.pascal_to_upper_case(pascal_case_value)
                result = deserialized_type[upper_case_value]  # noqa
                return result
            else:

                dict_value_annot_type = AnnotationsUtil.extract_dict_value_annot_type(type_)

                # Otherwise return a dictionary with recursively deserialized values
                result = {
                    k: (
                        v
                        if v.__class__.__name__ in self.primitive_type_names
                        else self.deserialize_data(v, dict_value_annot_type)
                    )
                    for k, v in data.items()
                }
                return result
        elif data.__class__.__name__ == "datetime":
            if type_ is None:
                return data

            if type_.__name__ == "datetime":
                return DatetimeUtil.round(data.replace(tzinfo=dt.timezone.utc))
            elif type_.__name__ == "date":
                return data.date()
            else:
                return data
        elif data.__class__.__name__ == "int":
            if type_ is not None and type_.__name__ == "float":
                return float(data)
            elif type_ is not None and type_.__name__ == "time":
                return TimeUtil.from_iso_int(data)
            else:
                return data
        elif data.__class__.__name__ == "Int64":
            return int(data)
        elif hasattr(data, "__iter__"):
            # Get the first item without iterating over the entire sequence
            first_item = next(iter(data), sentinel_value)

            # Get origin type and its args
            origin_type, iter_value_annot_type = AnnotationsUtil.extract_iterable_origin_and_args(type_)

            if first_item == sentinel_value:
                # Empty iterable, return None
                return None
            elif (
                iter_value_annot_type is not Any
                and first_item is not None
                and first_item.__class__.__name__ in self.primitive_type_names
            ):
                # Performance optimization to skip deserialization for arrays of primitive types
                # based on the type of first item (assumes that all remaining items are also primitive)

                # Convert list to tuple if it is annotated with Tuple[Type, ...]
                if isinstance(data, list) and origin_type is tuple:
                    return tuple(x for x in data)
                else:
                    return data
            else:
                # Deserialize each element of the iterable
                return origin_type(
                    (
                        v
                        if v.__class__.__name__ in self.primitive_type_names
                        else self.deserialize_data(v, iter_value_annot_type)
                    )
                    for v in data
                )

        elif is_key(data) or is_record(data):
            return data
        else:
            raise RuntimeError(f"Cannot deserialize data of type '{type(data)}'.")
