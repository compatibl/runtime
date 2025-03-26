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

import base64
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Type
from typing_extensions import Dict
from cl.runtime.file.file_data import FileData
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TDataDict
from cl.runtime.records.protocols import TDataField
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.annotations_util import AnnotationsUtil
from cl.runtime.serializers.dict_serializer import DictSerializer
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.slots_util import SlotsUtil
from cl.runtime.serializers.string_serializer import StringSerializer
from cl.runtime.serializers.string_serializer import primitive_type_names as str_primitive_type_names

_KEY_SERIALIZER = KeySerializers.DEFAULT


@dataclass(slots=True, kw_only=True)
class UiDictSerializer(DictSerializer):
    """Serialization for slots-based classes to ui format dict (legacy format)."""

    pascalize_keys: bool = True
    """pascalize_keys is True by default."""

    primitive_type_names = [
        "NoneType",
        "float",
        "bool",
    ]
    """Override primitive fields. In particular, str is not a primitive in ui format."""

    def serialize_data(self, data, annot_type: Type | None = None):

        if not self.pascalize_keys:
            raise RuntimeError("UI serialization format only supports pascalize_keys=True mode.")

        if data is None:
            return None

        if data.__class__.__name__ in self.primitive_type_names:
            return data
        elif data.__class__.__name__ in str_primitive_type_names:
            return StringSerializer.serialize_primitive(data)
        elif isinstance(data, Enum):
            # Serialize enum as its name
            serialized_enum = super(UiDictSerializer, self).serialize_data(data, annot_type)
            pascal_case_value = serialized_enum.get("_name")
            return pascal_case_value
        elif is_key(data):
            # Serialize key as string
            return _KEY_SERIALIZER.serialize(data)
        elif isinstance(data, dict):
            # Serialize dict as list of dicts in format [{"key": [key], "value": [value_as_legacy_variant]}]
            serialized_dict_items = []
            for k, v in super(UiDictSerializer, self).serialize_data(data, annot_type).items():
                # TODO (Roman): support more value types in dict

                # Apply custom format for None in dict
                if v is None:
                    serialized_dict_items.append({"key": k, "value": {"Empty": None}})
                    continue

                value_type = None
                if isinstance(v, str):
                    value_type = "String"
                elif isinstance(v, int):
                    value_type = "Int"
                elif isinstance(v, float):
                    value_type = "Double"
                elif isinstance(v, list):
                    serialized_dict_items.append([self.serialize_data(x) for x in v])
                elif isinstance(v, dict) and "_t" in v:
                    value_type = "Data"
                else:
                    raise ValueError(f"Value of type {type(v)} is not supported in dict ui serialization. Value: {v}.")

                if value_type is not None:
                    serialized_dict_items.append({"key": k, "value": {value_type: v}})

            return serialized_dict_items
        elif getattr(data, "__slots__", None) is not None:
            # Slots class, serialize as dictionary
            serialized_data = super(UiDictSerializer, self).serialize_data(data, annot_type)

            # Replace "_type" with "_t"
            if "_type" in serialized_data:
                serialized_data["_t"] = data.__class__.__name__
                del serialized_data["_type"]

            serialized_data = {k: v for k, v in serialized_data.items()}

            return serialized_data
        else:
            return super(UiDictSerializer, self).serialize_data(data, annot_type)

    def serialize_record_for_table(self, record: RecordProtocol) -> Dict[str, Any]:
        """
        Serialize record to ui table format.
        Contains only fields of supported types, _key and _t will be added based on record.
        """

        all_slots = SlotsUtil.get_slots(record.__class__)

        # Get subset of slots which supported in table format
        table_fields = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(slot)
            for slot in all_slots
            if (slot_v := getattr(record, slot))
            and (
                # TODO (Roman): check other types for table format
                # Check if field is primitive, key or enum
                slot_v.__class__.__name__ in (*self.primitive_type_names, "str")
                or is_key(slot_v)
                or isinstance(slot_v, Enum)
            )
        }

        # Serialize record to ui format and filter table fields
        table_dict = {k: v for k, v in self.serialize_data(record).items() if k in table_fields}

        # Add "_t" and "_key" attributes
        table_dict["_t"] = TypeUtil.name(record)
        table_dict["_key"] = _KEY_SERIALIZER.serialize(record)

        return table_dict

    @classmethod
    def _check_patch_binary_content(cls, data: TDataDict, short_type_name: str):
        """
        Handles binary data transformations.

        For BinaryData frontend, always return type as 'BinaryContent',
        so we need to patch the 'data' dict and rename attribute fields according to:
        :class:`cl.runtime.file.file_data.FileData` attributes naming.
        """

        if short_type_name == "BinaryContent":
            data["_type"] = FileData.__name__
            if content_value := data.pop("Content", None):  # type: str
                attr_name = CaseUtil.snake_to_pascal_case(FileData.file_bytes.__name__)
                data[attr_name] = base64.b64decode(content_value.encode())

    def deserialize_data(self, data: TDataField, type_: Type | None = None):

        if not self.pascalize_keys:
            raise RuntimeError("UI serialization format only supports pascalize_keys=True mode.")

        # Extract inner type if type_ is Optional[...]
        type_ = AnnotationsUtil.handle_optional_annot(type_)

        if isinstance(data, dict):
            # Copying data to ensure input dictionary is immutable
            data = data.copy()

            # Replace _t attribute to _type and deserialize with method in base class
            if short_type_name := data.pop("_t", None):
                # Apply additional conversion for BinaryContent
                self._check_patch_binary_content(data, short_type_name)

                if data.get("_type") is None:
                    data["_type"] = short_type_name
                return super(UiDictSerializer, self).deserialize_data(data, type_)
        elif isinstance(data, str):
            if type_ is None or type_ is Any:
                return data
            elif type_.__name__ in str_primitive_type_names:
                return StringSerializer.deserialize_primitive(data, type_)
            elif type_.__name__ in ("datetime", "date", "time"):
                return key_serializer.deserialize_primitive(data, type_)
            elif is_key(type_):
                # Deserialize key from string
                return _KEY_SERIALIZER.deserialize(data, type_)  # noqa
            elif issubclass(type_, Enum):
                # Deserialize enum from string using type in declaration
                return type_[CaseUtil.pascal_to_upper_case(data)]

        return super(UiDictSerializer, self).deserialize_data(data, type_)
