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
from uuid import UUID
from cl.runtime.records.conditions import Condition, ConditionField
from cl.runtime.records.query_mixin import QueryMixin
from stubs.cl.runtime.records.enum.stub_int_enum import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey


@dataclass(slots=True, kw_only=True)
class StubDataclassPrimitiveFieldsQuery(QueryMixin[StubDataclassPrimitiveFieldsKey]):
    """Stub record whose elements are primitive types."""

    key_str_field: Condition[str] | str | None = None
    """Stub field."""

    key_float_field: Condition[float] | float | None = None
    """Stub field."""

    key_bool_field: Condition[bool] | bool | None = None
    """Stub field."""

    key_int_field: Condition[int] | int | None = None
    """Stub field."""

    key_long_field: Condition[int] | int | None = None
    """The default is maximum safe signed int for JSON: 2^53 - 1."""

    key_date_field: Condition[dt.date] | dt.date | None = None
    """Stub field."""

    key_time_field: Condition[dt.time] | dt.time | None = None
    """Stub field."""

    key_date_time_field: Condition[dt.datetime] | dt.datetime | None = None
    """Stub field."""

    key_uuid_field: Condition[UUID] | UUID | None = None
    """Stub field."""

    key_bytes_field: Condition[bytes] | bytes | None = None
    """Stub field."""

    key_int_enum_field: Condition[StubIntEnum] | StubIntEnum | None = None
    """Stub field."""

    obj_str_field: Condition[str] | str | None = None
    """Stub field."""

    obj_str_with_eol_field: Condition[str] | str | None = None
    """Stub field."""

    obj_str_with_trailing_eol_field: Condition[str] | str | None = None
    """Stub field."""

    obj_str_timestamp_field: Condition[str] | str | None = None
    """Stub field."""

    obj_float_field: Condition[float] | float | None = None
    """Stub field."""

    obj_bool_field: Condition[bool] | bool | None = None
    """Stub field."""

    obj_int_field: Condition[int] | int | None = None
    """Stub field."""

    obj_long_field: Condition[int] | int | None = None
    """The default is maximum safe signed int for JSON: 2^53 - 1."""

    obj_date_field: Condition[dt.date] | dt.date | None = None
    """Stub field."""

    obj_time_field: Condition[dt.time] | dt.time | None = None
    """Stub field."""

    obj_date_time_field: Condition[dt.datetime] | dt.datetime | None = None
    """Stub field."""

    obj_uuid_field: Condition[UUID] | UUID | None = None
    """Stub field."""

    obj_bytes_field: Condition[bytes] | bytes | None = None
    """Stub field."""

    obj_bytes_large_field: Condition[bytes] | bytes | None = None
    """Stub field."""

    obj_int_enum_field: Condition[StubIntEnum] | StubIntEnum | None = None
    """Stub field."""
