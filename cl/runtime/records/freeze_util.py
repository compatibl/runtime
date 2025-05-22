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
from cl.runtime.records.protocols import MAPPING_CLASSES
from cl.runtime.records.protocols import PRIMITIVE_CLASSES
from cl.runtime.records.protocols import SEQUENCE_CLASSES
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.slots_util import SlotsUtil


class FreezeUtil:
    """Helper methods for freezable and frozen data types."""

    @classmethod
    def freeze(cls, data: Any) -> Any:
        """
        Recursively convert sequence classes to tuples and mapping classes to frozendicts inside nested data
        and invoke freeze method for buildable classes without checking the type hint.
        """
        if data is None or isinstance(data, PRIMITIVE_CLASSES) or isinstance(data, Enum):
            # Pass through None, primitive types, and enums
            return data
        elif isinstance(data, SEQUENCE_CLASSES):
            # Convert all sequence types to tuple
            return tuple(cls.freeze(item) for item in data)
        elif isinstance(data, MAPPING_CLASSES):
            # Convert all mapping types to frozendict
            return frozendict((k, cls.freeze(v)) for k, v in data.items())
        elif hasattr(data, "mark_frozen"):
            # Recreate with frozen fields and freeze the result
            return type(data)(**{k: cls.freeze(getattr(data, k)) for k in SlotsUtil.get_slots(type(data))}).mark_frozen()
        else:
            raise RuntimeError(
                f"Cannot freeze data of type {TypeUtil.name(data)} because it is not a\n"
                f"primitive type, enum, sequence, mapping or a freezable class."
            )
