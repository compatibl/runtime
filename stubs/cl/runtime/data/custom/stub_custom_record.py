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

from __future__ import annotations
from typing import Any, Dict, Optional
from cl.runtime.data.context import Context
from cl.runtime.data.record import Record
from stubs.cl.runtime.data.custom.stub_custom_record_key import StubCustomRecordKey


class StubCustomRecord(StubCustomRecordKey, Record):
    """Stub record used in tests."""

    base_field_str: Optional[str]
    """String attribute of base class."""

    base_field_float: Optional[float]
    """Float attribute of base class."""

    def __init__(self, *,
                 key_field_str: str = 'abc',
                 key_field_int: int = 123,
                 base_field_str: str = 'def',
                 base_field_float: float = 4.56):
        """Initialize instance attributes."""

        super().__init__(
            key_field_str = key_field_str,
            key_field_int = key_field_int
        )

        self.base_field_str = base_field_str
        self.base_field_float = base_field_float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary containing other dictionaries, lists and primitive types."""
        return super().to_dict() | {
            'base_field_str': self.base_field_str,
            'base_field_float': self.base_field_float,
        }
