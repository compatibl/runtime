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
from pathlib import Path
from typing import Iterable
import pandas as pd
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.csv_file_reader import CsvFileReader
from cl.runtime.records.data_util import DataUtil
from cl.runtime.records.freeze_util import FreezeUtil
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.type_util import TypeUtil
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


stub_entries: list[list[RecordProtocol]] = [  # noqa
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
    df.to_csv(file_path, index=False)


def save_test_records(entries: list[RecordProtocol]) -> tuple[list[RecordProtocol], Path]:
    file_path = Path(__file__).parent.joinpath(f"{TypeUtil.name(entries[0])}.csv")
    save_records_to_csv(entries, str(file_path.absolute()))
    return entries, file_path


def read_records_from_csv(file_path: Path, entry_type: type[RecordProtocol]):
    loader = CsvFileReader(file_path=str(file_path.absolute()))
    loader.csv_to_db()


def test_roundtrip(default_db_fixture):
    for test_entries in (*stub_entries,):
        file_path = None
        try:
            expected_entries, file_path = save_test_records(test_entries)
            entry_type = type(expected_entries[0])

            read_records_from_csv(file_path, entry_type)
            actual_records = tuple(active(DataSource).load_type(entry_type))
            assert actual_records == FreezeUtil.freeze(DataUtil.remove_none(expected_entries))
        finally:
            if file_path is not None:
                file_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])
