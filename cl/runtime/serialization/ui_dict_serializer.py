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
from cl.runtime.records.record_util import RecordUtil
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.dict_serializer import T
from cl.runtime.serialization.dict_serializer import _get_class_hierarchy_slots
from cl.runtime.serialization.dict_serializer import handle_optional_annot
from cl.runtime.serialization.string_serializer import StringSerializer

key_serializer = StringSerializer()


@dataclass(slots=True, kw_only=True)
class UiDictSerializer(DictSerializer):
    """Serialization for slot-based classes to ui format dict (legacy format)."""

    pascalize_keys: bool = True
    """pascalize_keys is True by default."""

    primitive_type_names = [
        "NoneType",
        "float",
        "int",
        "bool",
        "bytes",
        "UUID",
    ]
    """Override primitive fields. In particular, str is not a primitive in ui format."""

    def serialize_data(self, data):

        if not self.pascalize_keys:
            raise RuntimeError("UI serialization format only supports pascalize_keys=True mode.")

        if data is None:
            return None

        if data.__class__.__name__ == "str":
            return data
        elif isinstance(data, Enum):
            # Serialize enum as its name
            serialized_enum = super(UiDictSerializer, self).serialize_data(data)
            pascal_case_value = serialized_enum.get("_name")
            return pascal_case_value
        elif is_key(data):
            # Serialize key as string
            return key_serializer.serialize_key(data)
        elif isinstance(data, dict):
            # Serialize dict as list of dicts in format [{"key": [key], "value": [value_as_legacy_variant]}]
            serialized_dict_items = []
            for k, v in super(UiDictSerializer, self).serialize_data(data).items():
                # TODO (Roman): support more value types in dict

                # Apply custom format for None in dict
                if v is None:
                    serialized_dict_items.append({"key": k, "value": {"Empty": None}})
                    continue

                if isinstance(v, str):
                    value_type = "String"
                elif isinstance(v, int):
                    value_type = "Int"
                elif isinstance(v, float):
                    value_type = "Double"
                else:
                    raise ValueError(f"Value of type {type(v)} is not supported in dict ui serialization. Value: {v}.")

                serialized_dict_items.append({"key": k, "value": {value_type: v}})

            return serialized_dict_items
        elif getattr(data, "__slots__", None) is not None:

            # Invoke 'init' for each class in class hierarchy that implements it, in the order from base to derived
            RecordUtil.init_all(data)

            serialized_data = super(UiDictSerializer, self).serialize_data(data)

            # Replace "_type" with "_t"
            if "_type" in serialized_data:
                serialized_data["_t"] = data.__class__.__name__
                del serialized_data["_type"]

            serialized_data = {k: v for k, v in serialized_data.items()}

            return serialized_data
        else:
            return super(UiDictSerializer, self).serialize_data(data)

    def serialize_record_for_table(self, record: RecordProtocol) -> Dict[str, Any]:
        """
        Serialize record to ui table format.
        Contains only fields of supported types, _key and _t will be added based on record.
        """

        all_slots = _get_class_hierarchy_slots(record.__class__)

        # Get subset of slots which supported in table format
        table_slots = {
            slot: slot_v
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

        table_record = type(record)(**table_slots)  # noqa

        # Serialize record to ui format using table_slots
        table_dict: Dict[str, Any] = self.serialize_data(table_record)

        # Add "_t" and "_key" attributes
        table_dict["_t"] = record.__class__.__name__
        table_dict["_key"] = key_serializer.serialize_key(record.get_key())

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
            data["_t"] = FileData.__name__
            if content_value := data.pop("Content"):  # type: str
                attr_name = CaseUtil.snake_to_pascal_case(FileData.file_bytes.__name__)
                data[attr_name] = base64.b64decode(content_value.encode())

    def deserialize_data(self, data: TDataField, type_: Type[T] | None = None):

        if not self.pascalize_keys:
            raise RuntimeError("UI serialization format only supports pascalize_keys=True mode.")

        # Extract inner type if type_ is Optional[...]
        type_ = handle_optional_annot(type_)

        if isinstance(data, dict):
            # Copying data to ensure input dictionary is immutable
            data = data.copy()

            # Replace _t attribute to _type and deserialize with method in base class
            if short_type_name := data.pop("_t", None):
                # Apply additional conversion for BinaryContent
                self._check_patch_binary_content(data, short_type_name)

                data["_type"] = short_type_name
                return super(UiDictSerializer, self).deserialize_data(data, type_)
        elif isinstance(data, str):
            # TODO (Roman): Remove check for Any when no longer supported.
            if type_ is None or type_.__name__ == "str" or type_ is Any:
                return data
            elif is_key(type_):
                # Deserialize key from string
                return key_serializer.deserialize_key(data, type_)  # noqa
            elif issubclass(type_, Enum):
                # Deserialize enum from string using type in declaration
                return type_[CaseUtil.pascal_to_upper_case(data)]

        return super(UiDictSerializer, self).deserialize_data(data, type_)
