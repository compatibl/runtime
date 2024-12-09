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

from abc import ABC
from dataclasses import dataclass
from dataclasses import field


@dataclass(slots=True, kw_only=True)
class DataclassFreezable(ABC):
    """
    Derive from this class to add the ability to freeze the record from further modifications of its fields.
    Once frozen, the record cannot be unfrozen.
    """

    __frozen: bool = field(default=False, init=False)
    """
    Indicates the record is frozen so its fields can no longer be modified.
    Once frozen, the record cannot be unfrozen.
    """

    def freeze(self) -> None:
        """Freeze the record so its fields can no longer be modified. Once frozen, the record cannot be unfrozen."""
        object.__setattr__(self, "_DataclassFreezable__frozen", True)

    def __setattr__(self, key, value):
        """Override to check if the record is frozen."""
        if getattr(self, "_DataclassFreezable__frozen", False):
            raise AttributeError(f"Cannot modify field {type(self).__name__}.{key} because the record is frozen.")
        object.__setattr__(self, key, value)
