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

from pydantic import Field
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_data import StubPydanticData
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_key import StubPydanticKey


class StubPydanticNestedFields(StubPydanticKey, RecordMixin):

    generic_key_field: KeyMixin | None = Field(default_factory=StubPydanticKey)
    """Generic Key field."""

    key_field: StubPydanticKey | None = Field(default_factory=StubPydanticKey)
    """Key field."""

    data_field: StubPydanticData | None = Field(default_factory=StubPydanticData)
    """Data field."""

    enum_field: StubIntEnum | None = StubIntEnum.ENUM_VALUE_1
    """Enum field"""

    def get_key(self) -> KeyMixin:
        return StubPydanticKey(id=self.id).build()
