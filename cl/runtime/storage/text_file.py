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
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.contexts.lifecycle_mixin import LifecycleMixin
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class TextFile(DataclassMixin, LifecycleMixin, ABC):
    """Provides access to a local text file or text data in cloud storage via a common API."""

    @abstractmethod
    def read(self) -> str:
        """Read text."""

    @abstractmethod
    def write(self, text: str) -> None:
        """Write or append text."""
