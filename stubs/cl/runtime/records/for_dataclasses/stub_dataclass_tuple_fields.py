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
from typing import Tuple
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived


def stub_dataclass_str_tuple_factory() -> tuple[str, ...]:
    """Create stub values."""
    return "abc", "def"


def stub_dataclass_float_tuple_factory() -> tuple[float, ...]:
    """Create stub values."""
    return (
        0.0000123456789,
        0.000123456789,
        0.00123456789,
        0.0123456789,
        0.123456789,
        1.23456789,
        12.3456789,
        123.456789,
        1234.56789,
        12345.6789,
    )


def stub_dataclass_date_tuple_factory() -> tuple[dt.date, ...]:
    """Create stub values."""
    return (
        DateUtil.from_fields(2003, 4, 21),
        DateUtil.from_fields(2003, 5, 1),
    )


def stub_dataclass_data_tuple_factory() -> tuple[StubDataclassData, ...]:
    """Create stub values."""
    return (
        StubDataclassData(str_field="A", int_field=0),
        StubDataclassData(str_field="B", int_field=1),
    )


def stub_dataclass_key_tuple_factory() -> tuple[StubDataclassKey, ...]:
    """Create stub values."""
    return (
        StubDataclassKey(id="A"),
        StubDataclassKey(id="B"),
    )


def stub_dataclass_record_tuple_factory() -> tuple[StubDataclass, ...]:
    """Create stub values."""
    return (
        StubDataclass(id="A"),
        StubDataclass(id="B"),
    )


def stub_dataclass_derived_tuple_factory() -> tuple[StubDataclassDerived, ...]:
    """Create stub values."""
    return (
        StubDataclassDerived(id="A"),
        StubDataclassDerived(id="B"),
    )


@dataclass(slots=True, kw_only=True)
class StubDataclassTupleFields(StubDataclass):
    """Stub record whose elements are tuples."""

    str_tuple: tuple[str, ...] = required(default_factory=stub_dataclass_str_tuple_factory)
    """Stub field."""

    float_tuple: tuple[float, ...] = required(default_factory=stub_dataclass_float_tuple_factory)
    """Stub field."""

    date_tuple: tuple[dt.date, ...] = required(default_factory=stub_dataclass_date_tuple_factory)
    """Stub field."""

    data_tuple: tuple[StubDataclassData, ...] = required(default_factory=stub_dataclass_data_tuple_factory)
    """Stub field."""

    key_tuple: tuple[StubDataclassKey, ...] = required(default_factory=stub_dataclass_key_tuple_factory)
    """Stub field."""

    record_tuple: tuple[StubDataclass, ...] = required(default_factory=stub_dataclass_record_tuple_factory)
    """Stub field."""

    derived_tuple: tuple[StubDataclassDerived, ...] = required(default_factory=stub_dataclass_derived_tuple_factory)
    """Stub field."""
