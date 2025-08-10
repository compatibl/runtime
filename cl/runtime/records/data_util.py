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

from typing import Any
from cl.runtime.records.protocols import MAPPING_CLASSES
from cl.runtime.records.protocols import SEQUENCE_AND_MAPPING_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_CLASSES
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.serializers.slots_util import SlotsUtil


class DataUtil:
    """Helper methods for working with slotted classes."""

    @classmethod
    def is_empty(cls, data: Any) -> bool:
        """Check if the data is None, an empty string, or an empty container."""
        return data in (None, "") or (data.__class__.__name__ in SEQUENCE_AND_MAPPING_CLASS_NAMES and len(data) == 0)

    @classmethod
    def remove_none(cls, data: Any) -> Any:
        """Recursively remove dict (mapping) keys with None values, leave all other instances of None as is."""
        if is_data_key_or_record(data):
            return type(data)(
                **{
                    key: cls.remove_none(value)
                    for key in SlotsUtil.get_slots(type(data))
                    if (value := getattr(data, key, None)) is not None
                }
            )
        elif isinstance(data, MAPPING_CLASSES):
            return type(data)((key, cls.remove_none(value)) for key, value in data.items() if value is not None)
        elif isinstance(data, SEQUENCE_CLASSES):
            return type(data)(cls.remove_none(item) for item in data)
        else:
            return data
