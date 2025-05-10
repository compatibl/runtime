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
from cl.runtime.records.conditions import Condition
from cl.runtime.records.for_dataclasses.query import Query
from stubs.cl.runtime.records.enum.stub_int_enum import StubIntEnum


@dataclass(slots=True, kw_only=True)
class StubDataclassPrimitiveFieldsQuery(Query):
    """Stub record whose elements are primitive types."""

    key_str_field: Condition[str] | None = None
    """Stub field."""

    key_float_field: Condition[float] | None = None
    """Stub field."""

    key_bool_field: Condition[bool] | None = None
    """Stub field."""

    key_int_field: Condition[int] | None = None
    """Stub field."""

    key_long_field: Condition[int] | None = None
    """The default is maximum safe signed int for JSON: 2^53 - 1."""

    key_date_field: Condition[dt.date] | None = None
    """Stub field."""

    key_time_field: Condition[dt.time] | None = None
    """Stub field."""

    key_date_time_field: Condition[dt.datetime] | None = None
    """Stub field."""

    key_uuid_field: Condition[UUID] | None = None
    """Stub field."""

    key_bytes_field: Condition[bytes] | None = None
    """Stub field."""

    key_int_enum_field: Condition[StubIntEnum] | None = None
    """Stub field."""

    obj_str_field: Condition[str] | None = None
    """Stub field."""

    obj_str_with_eol_field: Condition[str] | None = None
    """Stub field."""

    obj_str_with_trailing_eol_field: Condition[str] | None = None
    """Stub field."""

    obj_str_timestamp_field: Condition[str] | None = None
    """Stub field."""

    obj_float_field: Condition[float] | None = None
    """Stub field."""

    obj_bool_field: Condition[bool] | None = None
    """Stub field."""

    obj_int_field: Condition[int] | None = None
    """Stub field."""

    obj_long_field: Condition[int] | None = None
    """The default is maximum safe signed int for JSON: 2^53 - 1."""

    obj_date_field: Condition[dt.date] | None = None
    """Stub field."""

    obj_time_field: Condition[dt.time] | None = None
    """Stub field."""

    obj_date_time_field: Condition[dt.datetime] | None = None
    """Stub field."""

    obj_uuid_field: Condition[UUID] | None = None
    """Stub field."""

    obj_bytes_field: Condition[bytes] | None = None
    """Stub field."""

    obj_bytes_large_field: Condition[bytes] | None = None
    """Stub field."""

    obj_int_enum_field: Condition[StubIntEnum] | None = None
    """Stub field."""
