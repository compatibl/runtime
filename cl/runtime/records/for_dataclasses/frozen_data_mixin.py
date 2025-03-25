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

from typing import Type
from typing_extensions import Self
from cl.runtime.records.clone_util import CloneUtil
from cl.runtime.records.protocols import TData


class FrozenDataMixin:
    """
    No-op implementations of DataProtocol for objects that are frozen on construction.
    Important - derive from this class only if the class has frozen=True or similar flag and
    all of its fields are also on construction.
    """

    def is_frozen(self) -> bool:  # noqa
        """Frozen on construction."""
        return True

    def mark_frozen(self) -> None:  # noqa
        """Frozen on construction, do nothing."""
        pass

    def build(self) -> Self:
        """Frozen on construction, do nothing."""
        pass

    def clone_as(self, result_type: Type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields of self."""
        return CloneUtil.clone_as(self, result_type)
