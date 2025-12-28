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
import os
import shutil
from typing import Iterable
import pandas as pd
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields

_CSV_SERIALIZER = DataSerializers.FOR_CSV
"""Serializer for CSV serialization."""


stub_entries: list[list[RecordMixin]] = [  # noqa
    [StubDataclass(id=f"abc1_n{i}").build() for i in range(5)],
    [StubDataclassNestedFields(id=f"abc2_n{i}").build() for i in range(5)],
    [StubDataclassComposite(primitive=f"abc{i}").build() for i in range(5)],
    [StubDataclassDerived(id=f"abc3_n{i}").build() for i in range(5)],
    [StubDataclassDoubleDerived(id=f"abc4_n{i}").build() for i in range(5)],
    [StubDataclassOtherDerived(id=f"abc5_n{i}").build() for i in range(5)],
    [StubDataclassOptionalFields(id=f"abc7_n{i}").build() for i in range(5)],
    [StubDataclassListFields(id=f"abc6_n{i}").build() for i in range(5)],
    [StubDataclassDictFields(id=f"abc8_n{i}").build() for i in range(5)],
    [StubDataclassDictListFields(id=f"abc9_n{i}").build() for i in range(5)],
    [StubDataclassListDictFields(id=f"abc10_n{i}").build() for i in range(5)],
    [StubDataclassPrimitiveFields(key_str_field=f"abc11_n{i}").build() for i in range(5)],
]
"""Stub entries for testing."""


def save_records_to_csv(records: Iterable, file_path: str) -> None:
    """Save records to file with specified path."""

    # Serialize records with flat serializer but use delimited serializer for keys
    record_dicts = []
    for rec in records:
        serialized_record = _CSV_SERIALIZER.serialize(rec)
        serialized_record.pop("_type", None)
        record_dicts.append(serialized_record)

    # Use pandas df to transform list of dicts to table format and write to file
    df = pd.DataFrame(record_dicts)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)


def save_test_records(entries: list[RecordMixin]) -> list[RecordMixin]:
    base_path = QaUtil.get_test_dir_from_call_stack()
    file_path = os.path.join(base_path, f"{typename(type(entries[0]))}.csv")
    save_records_to_csv(entries, file_path)
    return entries


def test_roundtrip(default_db_fixture):
    dir_path = QaUtil.get_test_dir_from_call_stack()
    for test_entries in (*stub_entries,):
        try:
            # Save to CSV
            expected_records = save_test_records(test_entries)

            # The same type for all records in this for loop iteration
            record_type = type(expected_records[0])

            # Load from CSV to DB
            csv_reader = CsvReader().build()
            record_type_pattern = f"{typename(record_type)}.*"
            records_from_csv = csv_reader.load_all(
                dirs=[dir_path],
                ext="csv",
                file_include_patterns=[record_type_pattern],
            )
            assert BuilderChecks.is_equal(records_from_csv, expected_records)
        finally:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


if __name__ == "__main__":
    pytest.main([__file__])
