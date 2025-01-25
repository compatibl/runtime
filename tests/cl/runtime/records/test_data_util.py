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
from dataclasses import dataclass
from cl.runtime.records.data_util import DataUtil


@dataclass(slots=True, kw_only=True)
class Base:
    _protected_base_field: str | None = None
    public_base_field_1: str | None = None
    public_base_field_2: str | None = None


@dataclass(slots=True, kw_only=True)
class Derived(Base):
    public_derived_field: str | None = None


def test_shallow_copy():
    """Test DataUtil.shallow_copy method."""

    # Create derived from base
    base = Base(public_base_field_1="public_base_field_1")
    derived = DataUtil.shallow_copy(Derived, base)

    # Public fields in base, only one is set
    assert derived.public_base_field_1 == base.public_base_field_1
    assert derived.public_base_field_2 is None

    # Protected fields in base, not set
    assert derived._protected_base_field is None

    # Public fields in derived, not set
    assert derived.public_derived_field is None


if __name__ == "__main__":
    pytest.main([__file__])
