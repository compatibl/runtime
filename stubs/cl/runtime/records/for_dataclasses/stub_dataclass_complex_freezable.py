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

from dataclasses import dataclass, field
from typing import List

from cl.runtime.records.for_dataclasses.freezable import Freezable
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_simple_freezable import StubDataclassSimpleFreezable


@dataclass(slots=True, kw_only=True)
class StubDataclassComplexFreezable(Freezable):
    """Freezable class stub."""

    value: str = "abc"
    """String value."""

    freezable_obj: StubDataclassSimpleFreezable = field(default_factory=lambda: StubDataclassSimpleFreezable())
    """Embedded freezable object, will be frozen."""

    nonfreezable_obj: StubDataclassData = field(default_factory=lambda: StubDataclassData())
    """Embedded non-freezable object, will be frozen."""

    nonfreezable_list: List[StubDataclassSimpleFreezable] = field(default_factory=lambda: [
        StubDataclassSimpleFreezable(),
        StubDataclassSimpleFreezable(),
    ])
    """Embedded non-freezable list of freezable objects, list items will not be frozen."""
