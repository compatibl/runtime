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
from typing import Any, List

from typing_extensions import Dict

from cl.runtime.records.protocols import is_key, RecordProtocol
from cl.runtime.serialization.dict_serializer import DictSerializer, _get_class_hierarchy_slots
from cl.runtime.serialization.string_serializer import StringSerializer


class UiDictSerializer(DictSerializer):

    def serialize_data(self, data, select_fields: List[str] | None = None):
        # TODO (Roman): make serialization format deserializable

        if data is None:
            return None

        if data.__class__.__name__ in self.primitive_type_names:
            return data
        elif isinstance(data, Enum):
            # serialize enum as its name
            serialized_enum = super().serialize_data(data, select_fields)
            return serialized_enum.get('_name')
        elif is_key(data):
            # serialize key as ';' delimited string
            return ";".join((getattr(data, slot) for slot in data.__slots__))
        elif isinstance(data, dict):
            # serialize dict as list of dicts in format [{"key": [key], "value": [value_as_legacy_variant]}]
            serialized_dict_items = []
            for k, v in super().serialize_data(data).items():
                # TODO (Roman): support more value types in dict
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
        else:
            return super().serialize_data(data, select_fields)

    def serialize_data_for_table(self, data: RecordProtocol) -> Dict[str, Any]:

        key_serializer = StringSerializer()
        all_slots = _get_class_hierarchy_slots(data.__class__)

        table_slots = [
            slot for slot in all_slots
            if (slot_v := getattr(data, slot))
            and (
                slot_v.__class__.__name__ in self.primitive_type_names
                or is_key(slot_v)
                or isinstance(slot_v, Enum)
            )
        ]

        table_record = super().serialize_data(data, select_fields=table_slots)
        table_record["_t"] = data.__class__.__name__
        table_record["_key"] = key_serializer.serialize_key(data.get_key())

        return table_record