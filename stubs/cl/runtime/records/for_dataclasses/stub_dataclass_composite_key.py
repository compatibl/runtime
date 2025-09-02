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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclassKey


@dataclass(slots=True)
class StubDataclassCompositeKey(DataclassMixin, KeyMixin):
    """Stub for a composite key that contains other key fields."""

    primitive: str = "abc"
    """String key element."""

    embedded_1: StubDataclassKey = required(default_factory=lambda: StubDataclassKey(id="def"))
    """Embedded key 1."""

    embedded_2: StubDataclassKey = required(default_factory=lambda: StubDataclassKey(id="xyz"))
    """Embedded key 2."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return StubDataclassCompositeKey
