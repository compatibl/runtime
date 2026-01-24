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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.storage.delete_request import DeleteRequest
from cl.runtime.routers.storage.delete_response_util import DeleteResponseUtil
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived


def test_method(default_db_fixture):
    """Test coroutine for /storage/delete route."""

    existing_records = [
        StubDataclassDerived(id=f"existing_record_{i}", derived_str_field=f"value_{i}").build() for i in range(5)
    ]
    active(DataSource).replace_many(existing_records, commit=True)

    delete_records_payload = {
        "delete_keys": [{"key": record.id, "type": "StubDataclassDerived"} for record in existing_records[:3]]
    }
    delete_records_request_obj = DeleteRequest(**delete_records_payload)

    delete_records_result = DeleteResponseUtil.delete_records(delete_records_request_obj)
    records_in_db = sorted(active(DataSource).load_by_type(StubDataclassDerived), key=lambda x: x.id)

    # Check if result is a list[KeyRequestItem] object.
    assert isinstance(delete_records_result, list)
    assert all(isinstance(x, KeyRequestItem) for x in delete_records_result)

    # Check that the number of records in the DB is correct.
    assert len(records_in_db) == 2
    # Check that the first 3 records are deleted.
    for non_deleted_record, record_in_db in zip(existing_records[3:], records_in_db):
        assert non_deleted_record.id == record_in_db.id
        assert non_deleted_record.derived_str_field == record_in_db.derived_str_field


def test_api(default_db_fixture):
    """Test REST API for /storage/delete route."""
    with QaClient() as test_client:
        existing_records = [
            StubDataclassDerived(id=f"existing_record_{i}", derived_str_field=f"value_{i}").build() for i in range(5)
        ]
        active(DataSource).replace_many(existing_records, commit=True)

        delete_records_payload = [{"Key": record.id, "Type": "StubDataclassDerived"} for record in existing_records[:3]]

        delete_records_response = test_client.post(
            "/storage/delete",
            json=delete_records_payload,
        )
        delete_records_json = delete_records_response.json()
        records_in_db = sorted(active(DataSource).load_by_type(StubDataclassDerived), key=lambda x: x.id)

        assert delete_records_response.status_code == 200
        assert isinstance(delete_records_json, list)
        assert len(delete_records_json) == 3

        # Check that the number of records in the DB is correct.
        assert len(records_in_db) == 2
        # Check that the first 3 records are deleted.
        for non_deleted_record, record_in_db in zip(existing_records[3:], records_in_db):
            assert non_deleted_record.id == record_in_db.id
            assert non_deleted_record.derived_str_field == record_in_db.derived_str_field


if __name__ == "__main__":
    pytest.main([__file__])
