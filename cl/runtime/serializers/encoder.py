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
from typing import Any
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class Encoder(DataclassMixin, ABC):
    """Abstract base class of encoders that convert data to string and back."""

    @abstractmethod
    def encode(self, data: Any) -> str | None:
        """Encode to a string, pass through None."""

    @abstractmethod
    def decode(self, data: str | bytes | None) -> Any:
        """Decode from a string or bytes, pass through None."""

    def normalize(self, data: Any) -> Any:
        """Recursively normalize serialized data (dicts, lists, strings) for character encoding."""
        if isinstance(data, dict):
            # Recursively normalize dictionary keys and values
            return {CharUtil.normalize(k): self.normalize(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively normalize list items
            return [self.normalize(item) for item in data]
        elif isinstance(data, str):
            # Normalize string values, converting empty strings to None
            return CharUtil.normalize_or_none(data)
        else:
            # Return other types (int, float, bool, None) as-is
            return data
