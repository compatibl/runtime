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

from typing import Any, TypeVar
from typing import Type
from cl.runtime.records.type_util import TypeUtil

T = TypeVar("T")


class DataUtil:
    """Utilities for working with dataclasses and similar frameworks."""

    @classmethod
    def shallow_copy(cls, target_type: Type[T], source: Any) -> T:
        """
        Create an instance of target_type with shallow copy of all public fields from source.
        
        Notes:
          - The method does not copy protected or private fields (fields starting with '_')
          - Error message if target_type is missing some of the public fields of source
          - DataUtil helper works only with slots-based classes
        """
        if not (source_slots := getattr((source_type := type(source)), "__slots__", None)):
            raise RuntimeError(f"An object with type {TypeUtil.name(source_type)} used as\n"
                               f"source in 'DataUtil.shallow_copy' method has no slots.\n"
                               f"DataUtil helper works only with slots-based classes.")
        return target_type(**{slot: getattr(source, slot) for slot in source_slots if not slot.startswith("_")})
