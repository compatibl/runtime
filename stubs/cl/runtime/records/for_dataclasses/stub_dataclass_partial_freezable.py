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

from dataclasses import dataclass
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_non_freezable import StubDataclassNonFreezable


@dataclass(slots=True, kw_only=True)
class StubDataclassPartialFreezable(DataclassMixin):
    """Freezable class must not have a non-freezable class field, should raise."""

    value: str = "abc"
    """String value."""

    freezable_obj: StubDataclassData = required(default_factory=lambda: StubDataclassData())
    """Embedded freezable object."""

    non_freezable_obj: StubDataclassNonFreezable = required(default_factory=lambda: StubDataclassNonFreezable())
    """Embedded non-freezable object, will cause an error when attempting to freeze."""
