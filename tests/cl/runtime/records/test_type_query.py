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

import pytest
from cl.runtime.records.type_query import TypeQuery
from cl.runtime.records.type_util import TypeUtil
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey


def test_type_query():
    """Test for TypeQuery class."""

    # No dynamic tables
    assert TypeQuery(StubDataclass).build().get_target_type() == StubDataclass

    # Has dynamic tables (overrides get_table)
    with pytest.raises(Exception):
        TypeQuery(StubDataclassPolymorphicKey).build()

if __name__ == "__main__":
    pytest.main([__file__])
