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

from cl.runtime.records.for_dataclasses.data_query import DataQuery
from cl.runtime.records.for_dataclasses.key_query import KeyQuery
from cl.runtime.records.for_dataclasses.query import Query
from cl.runtime.records.query_mixin import QueryMixin
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_data import StubDataclassDerivedData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_from_derived_data import (
    StubDataclassDerivedFromDerivedData,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecordKey


@dataclass(slots=True, kw_only=True)
class StubDataclassNestedFieldsQuery(Query, QueryMixin[StubDataclassNestedFields]):
    """Stub derived class."""

    base_field: DataQuery[StubDataclassData] | None = None
    """Stub field."""

    derived_field: DataQuery[StubDataclassDerivedData] | None = None
    """Stub field."""

    derived_from_derived_field: DataQuery[StubDataclassDerivedFromDerivedData] | None = None
    """Stub field."""

    polymorphic_field: DataQuery[StubDataclassData] | None = None
    """Declared StubDataclassData but provided an instance of StubDataclassDerivedData."""

    polymorphic_derived_field: DataQuery[StubDataclassDerivedData] | None = None
    """Declared StubDataclassDerivedData but provided an instance of StubDataclassDerivedFromDerivedData."""

    key_field: KeyQuery[StubDataclassRecordKey] | None = None
    """Stub field."""

    record_as_key_field: KeyQuery[StubDataclassRecordKey] | None = None
    """Stub field with key type initialized to record type instance."""
