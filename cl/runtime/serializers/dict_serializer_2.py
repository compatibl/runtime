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
from typing import Any, Type
from frozendict import frozendict
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_util import RecordUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.schema import Schema
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.serializers.annotations_util import AnnotationsUtil
from cl.runtime.serializers.dict_serializer import get_type_dict
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.serializers.sentinel_type import sentinel_value
from cl.runtime.records.protocols import _PRIMITIVE_TYPE_NAMES, TDataField, is_primitive, is_key, is_record


@dataclass(slots=True, kw_only=True)
class DictSerializer2(Freezable):
    """Roundtrip serialization of object to dictionary with optional type information."""

    primitive_serializer: PrimitiveSerializer | None = None
    """Use to serialize primitive types if set, otherwise leave primitive types unchanged."""

    enum_serializer: EnumSerializer | None = None
    """Use to serialize enum types if set, otherwise leave enum types unchanged."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    omit_type: bool | None = None
    """Serialize without including _type in output and deserialize into dict/list even if _type is specified."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.enum_serializer is None:
            # Create an EnumSerializer with default settings if not specified
            self.enum_serializer = EnumSerializer().build()

    def to_dict(self, data: Any, schema_type: Type | None = None) -> Any:
        """
        Serialize a slots-based object to a dictionary. Type information is written only if omit_type is not set.

        - If (a) data_type is None or (b) matches type(data) or (c) omit_type is set, do not write the _type field
        - Otherwise, check that data is an instance of data_type and write TypeUtil.name(data) to the _type field

        Args:
            data: Data to serialize which may be a class with build method, sequence, mapping, or a primitive type
            schema_type: Type of the object specified in the schema (optional)
        """

        if getattr(data, "__slots__", None) is not None:

            # If type is specified, ensure that data is an instance of the specified type
            if schema_type and not isinstance(data, schema_type):
                obj_type_name = TypeUtil.name(data.__class__)
                schema_type_name = TypeUtil.name(schema_type)
                raise RuntimeError(f"Type {obj_type_name} is not the same or a subclass of "
                                   f"the type {schema_type_name} specified in schema.")

            # Write type information if omit_type is False and type_ is not specified or is not type(data)
            if (not self.omit_type) and (schema_type is None or schema_type is data.__class__):
                obj_type_name = TypeUtil.name(data.__class__)
                result = {}  # {"_type": obj_type_name}
            else:
                result = {}

            # Get slots from this class and its bases in the order of declaration from base to derived
            type_decl = TypeDecl.for_type(data.__class__)
            field_types = [
                (
                    field.name,
                    Schema.get_type_by_short_name(field.field_type_decl.name),
                )
                for field in type_decl.fields
            ]

            # Serialize slot values in the order of declaration except those that are None
            result.update({
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                    if isinstance(v, Enum)
                    else self.to_dict(v)
                )
                for k, t in field_types
                if (v := getattr(data, k)) is not None and (not hasattr(v, "__len__") or len(v) > 0)
            })
            return result
        elif isinstance(data, list) or isinstance(data, tuple):
            # Assume that type of the first item is the same as for the rest of the collection
            is_primitive_collection = len(data) > 0 and data[0].__class__.__name__ in _PRIMITIVE_TYPE_NAMES
            if is_primitive_collection:
                # More efficient implementation for a primitive collection
                if self.primitive_serializer is not None:
                    return [self.primitive_serializer.serialize(v) for v in data]
                else:
                    return data
            else:
                # Not a primitive collection, serialize elements one by one
                result = [
                    None if v is None else
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                    if isinstance(v, Enum)
                    else self.to_dict(v)
                    for v in data
                ]
            return result
        elif isinstance(data, dict) or isinstance(data, frozendict):
            # Dictionary, return with serialized values except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in _PRIMITIVE_TYPE_NAMES
                    else (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                    if isinstance(v, Enum)
                    else self.to_dict(v)
                )
                for k, v in data.items()
                if v is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def from_dict(self, data: TDataField, schema_type: Type | None = None) -> Any:
        """Deserialize a dictionary into object using _type and schema."""

        # Extract inner type if type_ is Optional[...]
        schema_type = AnnotationsUtil.handle_optional_annot(schema_type)

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
                        if v is None or is_primitive(v)
                        else self.from_dict(
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

                dict_value_annot_type = AnnotationsUtil.extract_dict_value_annot_type(schema_type)

                # Otherwise return a dictionary with recursively deserialized values
                result = {
                    k: (
                        v
                        if v is None or is_primitive(v)
                        else self.from_dict(v, dict_value_annot_type)
                    )
                    for k, v in data.items()
                }
                return result
        elif data.__class__.__name__ == "datetime":
            if schema_type is None:
                return data

            if schema_type.__name__ == "datetime":
                return DatetimeUtil.round(data.replace(tzinfo=dt.timezone.utc))
            elif schema_type.__name__ == "date":
                return data.date()
            else:
                return data
        elif data.__class__.__name__ == "int":
            if schema_type is not None and schema_type.__name__ == "float":
                return float(data)
            elif schema_type is not None and schema_type.__name__ == "time":
                return TimeUtil.from_iso_int(data)
            else:
                return data
        elif data.__class__.__name__ == "Int64":
            return int(data)
        elif hasattr(data, "__iter__"):
            # Get the first item without iterating over the entire sequence
            first_item = next(iter(data), sentinel_value)

            # Get origin type and its args
            origin_type, iter_value_annot_type = AnnotationsUtil.extract_iterable_origin_and_args(schema_type)

            if first_item == sentinel_value:
                # Empty iterable, return None
                return None
            elif (
                iter_value_annot_type is not Any
                and first_item is not None
                and is_primitive(first_item)
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
                result = origin_type(
                    (
                        v
                        if v is None or is_primitive(v)
                        else self.from_dict(v, iter_value_annot_type)
                    )
                    for v in data
                )
                return result

        elif is_key(data) or is_record(data):
            return data
        else:
            raise RuntimeError(f"Cannot deserialize data of type '{type(data)}'.")
