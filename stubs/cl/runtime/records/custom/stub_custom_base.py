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

from cl.runtime.records.record_mixin import RecordMixin
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Type

StubCustomBaseKey = Tuple[Type["StubCustomBase"], str, int]


class StubCustomBase(RecordMixin):
    """Stub record used in tests."""

    str_field: Optional[str]
    """First primary key attribute."""

    int_field: Optional[int]
    """Second primary key attribute."""

    float_field: Optional[float]
    """Float attribute of base class."""

    def __init__(self, *, str_field: str = "abc", int_field: int = 123, float_field: float = 4.56):
        """Initialize instance attributes."""

        self.str_field = str_field
        self.int_field = int_field
        self.float_field = float_field

    def pack(self) -> Tuple[StubCustomBaseKey, Type[StubCustomBase], Dict[str, Any]]:
        class_type = type(self)
        return (
            self.get_key(),
            StubCustomBase,
            {
                "str_field": self.str_field,
                "int_field": self.int_field,
                "float_field": self.float_field,
            },
        )

    def get_key(self) -> StubCustomBaseKey:
        return StubCustomBase, self.str_field, self.int_field