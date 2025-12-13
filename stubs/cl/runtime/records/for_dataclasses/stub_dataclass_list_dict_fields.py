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
from typing import Dict
from typing import List
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_data_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_date_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_derived_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_float_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import (
    stub_dataclass_float_or_none_list_factory,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_key_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_record_list_factory
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import stub_dataclass_str_list_factory


def stub_dataclass_str_list_dict_factory() -> dict[str, list[str]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_str_list_factory(),
        "b": stub_dataclass_str_list_factory(),
    }


def stub_dataclass_float_list_dict_factory() -> dict[str, list[float]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_float_list_factory(),
        "b": stub_dataclass_float_list_factory(),
    }


def stub_dataclass_float_list_or_none_dict_factory() -> dict[str, list[float] | None]:
    """Create stub values."""
    return {
        "a": None,
        "b": stub_dataclass_float_list_factory(),
        "c": None,
    }


def stub_dataclass_float_or_none_list_dict_factory() -> dict[str, list[float | None]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_float_or_none_list_factory(),
        "b": stub_dataclass_float_or_none_list_factory(),
    }


def stub_dataclass_date_list_dict_factory() -> dict[str, list[dt.date]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_date_list_factory(),
        "b": stub_dataclass_date_list_factory(),
    }


def stub_dataclass_data_list_dict_factory() -> dict[str, list[StubDataclassData]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_data_list_factory(),
        "b": stub_dataclass_data_list_factory(),
    }


def stub_dataclass_key_list_dict_factory() -> dict[str, list[StubDataclassKey]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_key_list_factory(),
        "b": stub_dataclass_key_list_factory(),
    }


def stub_dataclass_record_list_dict_factory() -> dict[str, list[StubDataclass]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_record_list_factory(),
        "b": stub_dataclass_record_list_factory(),
    }


def stub_dataclass_derived_list_dict_factory() -> dict[str, list[StubDataclassDerived]]:
    """Create stub values."""
    return {
        "a": stub_dataclass_derived_list_factory(),
        "b": stub_dataclass_derived_list_factory(),
    }


@dataclass(slots=True, kw_only=True)
class StubDataclassListDictFields(StubDataclass):
    """Stub record whose elements are dictionaries."""

    float_list_dict: dict[str, list[float]] = required(default_factory=stub_dataclass_float_list_dict_factory)
    """Stub field."""

    float_or_none_list_dict: dict[str, list[float | None]] = required(
        default_factory=stub_dataclass_float_or_none_list_dict_factory,
    )
    """Stub field."""

    float_list_or_none_dict: dict[str, list[float] | None] = required(
        default_factory=stub_dataclass_float_list_or_none_dict_factory,
    )
    """Stub field."""

    float_list_dict_or_none: dict[str, list[float]] | None = optional(
        default_factory=stub_dataclass_float_list_dict_factory,
    )
    """Stub field."""

    date_list_dict: dict[str, list[dt.date]] = required(default_factory=stub_dataclass_date_list_dict_factory)
    """Stub field."""

    record_list_dict: dict[str, list[StubDataclass]] = required(
        default_factory=stub_dataclass_record_list_dict_factory,
    )
    """Stub field."""

    derived_list_dict: dict[str, list[StubDataclassDerived]] = required(
        default_factory=stub_dataclass_derived_list_dict_factory,
    )
    """Stub field."""
