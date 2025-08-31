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

import datetime as dt
from dataclasses import dataclass
from frozendict import frozendict
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived


def stub_dataclass_str_frozendict_factory() -> frozendict[str, str]:
    """Create stub values."""
    return frozendict({"a": "abc", "b": "def"})


def stub_dataclass_float_frozendict_factory() -> frozendict[str, float]:
    """Create stub values."""
    return frozendict(
        {
            "a": 0.0000123456789,
            "b": 0.000123456789,
            "c": 0.00123456789,
            "d": 0.0123456789,
            "e": 0.123456789,
            "f": 1.23456789,
            "g": 12.3456789,
            "h": 123.456789,
            "i": 1234.56789,
            "j": 12345.6789,
        }
    )


def stub_dataclass_date_frozendict_factory() -> frozendict[str, dt.date]:
    """Create stub values."""
    return frozendict(
        {
            "a": DateUtil.from_fields(2003, 4, 21),
            "b": DateUtil.from_fields(2003, 5, 1),
        }
    )


def stub_dataclass_data_frozendict_factory() -> frozendict[str, StubDataclassData]:
    """Create stub values."""
    return frozendict(
        {
            "a": StubDataclassData(str_field="A", int_field=1),
            "b": StubDataclassData(str_field="B", int_field=2),
        }
    )


def stub_dataclass_key_frozendict_factory() -> frozendict[str, StubDataclassKey]:
    """Create stub values."""
    return frozendict(
        {
            "a": StubDataclassKey(id="A"),
            "b": StubDataclassKey(id="B"),
        }
    )


def stub_dataclass_record_frozendict_factory() -> frozendict[str, StubDataclass]:
    """Create stub values."""
    return frozendict(
        {
            "a": StubDataclass(id="A"),
            "b": StubDataclass(id="B"),
        }
    )


def stub_dataclass_derived_frozendict_factory() -> frozendict[str, StubDataclassDerived]:
    """Create stub values."""
    return frozendict(
        {
            "a": StubDataclassDerived(id="A"),
            "b": StubDataclassDerived(id="B"),
        }
    )


@dataclass(slots=True, kw_only=True)
class StubDataclassFrozendictFields(StubDataclass):
    """Stub record whose elements are frozendicts."""

    str_frozendict: frozendict[str, str] = required(default_factory=stub_dataclass_str_frozendict_factory)
    """Stub field."""

    float_frozendict: frozendict[str, float] = required(default_factory=stub_dataclass_float_frozendict_factory)
    """Stub field."""

    date_frozendict: frozendict[str, dt.date] = required(default_factory=stub_dataclass_date_frozendict_factory)
    """Stub field."""

    data_frozendict: frozendict[str, StubDataclassData] = required(
        default_factory=stub_dataclass_data_frozendict_factory
    )
    """Stub field."""

    key_frozendict: frozendict[str, StubDataclassKey] = required(default_factory=stub_dataclass_key_frozendict_factory)
    """Stub field."""

    record_frozendict: frozendict[str, StubDataclass] = required(
        default_factory=stub_dataclass_record_frozendict_factory
    )
    """Stub field."""

    derived_frozendict: frozendict[str, StubDataclassDerived] = required(
        default_factory=stub_dataclass_derived_frozendict_factory
    )
    """Stub field."""
