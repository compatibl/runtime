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
import orjson
import os
import shutil
from typing import Iterable
from cl.runtime.file.json_reader import JsonReader
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

_JSON_SERIALIZER = DataSerializers.FOR_JSON
"""Serializer for JSON serialization (returns dict, not string)."""


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


def save_records_to_json(records: Iterable[RecordMixin], file_path: str, *, include_type: bool = True) -> None:
    """Save records to JSON file with specified path."""
    record_dicts = []
    for rec in records:
        serialized_record = _JSON_SERIALIZER.serialize(rec)
        if not include_type:
            serialized_record.pop("_type", None)
        record_dicts.append(serialized_record)

    # Write JSON array to file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="wb") as file:
        file.write(orjson.dumps(record_dicts, option=orjson.OPT_INDENT_2))


def save_single_record_to_json(record: RecordMixin, file_path: str, *, include_type: bool = True) -> None:
    """Save single record to JSON file (as dict, not array)."""
    serialized_record = _JSON_SERIALIZER.serialize(record)
    if not include_type:
        serialized_record.pop("_type", None)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode="wb") as file:
        file.write(orjson.dumps(serialized_record, option=orjson.OPT_INDENT_2))


def test_roundtrip_with_type_field():
    """Test JSON roundtrip where _type field is included in JSON (default serializer behavior)."""
    dir_path = QaUtil.get_test_dir_from_call_stack()

    for test_entries in stub_entries:
        try:
            expected_records = test_entries
            record_type = type(expected_records[0])

            # Save to JSON with _type field
            file_path = os.path.join(dir_path, f"{typename(record_type)}.json")
            save_records_to_json(expected_records, file_path, include_type=True)

            # Load from JSON
            json_reader = JsonReader().build()
            record_type_pattern = f"{typename(record_type)}.*"
            records_from_json = json_reader.load_all(
                dirs=[dir_path],
                ext="json",
                file_include_patterns=[record_type_pattern],
            )

            # Verify
            assert BuilderChecks.is_equal(records_from_json, expected_records)
        finally:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


def test_roundtrip_without_type_field():
    """Test JSON roundtrip where _type field is omitted, relying on filename for type."""
    dir_path = QaUtil.get_test_dir_from_call_stack()

    for test_entries in stub_entries:
        try:
            expected_records = test_entries
            record_type = type(expected_records[0])

            # Save to JSON without _type field (relying on filename)
            file_path = os.path.join(dir_path, f"{typename(record_type)}.json")
            save_records_to_json(expected_records, file_path, include_type=False)

            # Load from JSON - should infer type from filename
            json_reader = JsonReader().build()
            record_type_pattern = f"{typename(record_type)}.*"
            records_from_json = json_reader.load_all(
                dirs=[dir_path],
                ext="json",
                file_include_patterns=[record_type_pattern],
            )

            # Verify
            assert BuilderChecks.is_equal(records_from_json, expected_records)
        finally:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


def test_roundtrip_single_record():
    """Test JSON roundtrip with a single record (dict instead of array)."""
    dir_path = QaUtil.get_test_dir_from_call_stack()

    try:
        # Use a single record
        expected_record = StubDataclass(id="single_record_test").build()
        record_type = type(expected_record)

        # Save single record as JSON object (not array) - use typename for PascalCase compliance
        file_path = os.path.join(dir_path, f"{typename(record_type)}.json")
        save_single_record_to_json(expected_record, file_path, include_type=True)

        # Load from JSON - should handle single object
        json_reader = JsonReader().build()
        records_from_json = json_reader.load_all(
            dirs=[dir_path],
            ext="json",
        )

        # Verify
        assert len(records_from_json) == 1
        assert BuilderChecks.is_equal(records_from_json[0], expected_record)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)


def test_roundtrip_mixed_types():
    """Test JSON roundtrip with mixed types in the same file (using _type field)."""
    dir_path = QaUtil.get_test_dir_from_call_stack()

    try:
        # Create a mix of different types
        expected_records = [
            StubDataclass(id="mixed_1").build(),
            StubDataclassDerived(id="mixed_2").build(),
            StubDataclassDoubleDerived(id="mixed_3").build(),
        ]

        # Save with _type field (required for mixed types)
        file_path = os.path.join(dir_path, "StubDataclassMixed.json")
        save_records_to_json(expected_records, file_path, include_type=True)

        # Load from JSON
        json_reader = JsonReader().build()
        records_from_json = json_reader.load_all(
            dirs=[dir_path],
            ext="json",
        )

        # Verify all records loaded correctly
        assert len(records_from_json) == len(expected_records)
        assert BuilderChecks.is_equal(records_from_json, expected_records)
    finally:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)


if __name__ == "__main__":
    pytest.main([__file__])


