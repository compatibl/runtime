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
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.save_request import SaveRequest
from cl.runtime.routers.storage.save_response_util import SaveResponseUtil
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey

# Test save record payloads
create_record_payload = {"Id": "new_record", "DerivedStrField": "test", "_t": "StubDataclassDerived"}

update_record_payload = {
    "Id": "existing_record",
    "DerivedStrField": "new_value",
    "_t": "StubDataclassDerived",
}


def test_method(pytest_default_db):
    """Test coroutine for /storage/save route."""

    # Test saving new record.
    save_new_record_request_obj = SaveRequest(records=[create_record_payload])

    save_new_record_result = SaveResponseUtil.save_records(save_new_record_request_obj)

    # Check if result is a list[KeyRequestItem] object.
    assert isinstance(save_new_record_result, list)
    assert all(isinstance(response_item, KeyRequestItem) for response_item in save_new_record_result)
    assert len(save_new_record_result) == 1
    assert save_new_record_result[0].key == "new_record"

    new_key = StubDataclassKey(id="new_record").build()
    new_record_in_db = DbContext.load_one(new_key, cast_to=StubDataclassDerived)
    records_count = len(list(DbContext.load_type(StubDataclassDerived)))

    assert new_record_in_db is not None
    assert new_record_in_db.id == "new_record"
    assert new_record_in_db.derived_str_field == "test"

    # DB should only contain the created record.
    assert records_count == 1

    # Test updating existing record.
    existing_record = StubDataclassDerived(id="existing_record", derived_str_field="old_value").build()
    DbContext.save_one(existing_record)
    update_record_request_obj = SaveRequest(records=[update_record_payload])

    update_record_result = SaveResponseUtil.save_records(update_record_request_obj)
    existing_key = StubDataclassKey(id="existing_record").build()

    # Check if result is a list[KeyRequestItem] object.
    assert isinstance(update_record_result, list)
    assert all(isinstance(response_item, KeyRequestItem) for response_item in update_record_result)
    assert len(update_record_result) == 1
    # Check that response contains the key of the new record.
    assert update_record_result[0].key == "existing_record"

    updated_record_in_db = DbContext.load_one(existing_key, cast_to=StubDataclassDerived)
    records_count = len(list(DbContext.load_type(StubDataclassDerived)))
    assert updated_record_in_db is not None
    assert updated_record_in_db.id == "existing_record"
    assert updated_record_in_db.derived_str_field == "new_value"
    # DB should only contain the created record + the updated record.
    assert records_count == 2


def test_api(pytest_default_db):
    """Test REST API for /storage/save route."""
    with QaClient() as test_client:
        # Test saving new record

        save_new_record_response = test_client.post(
            "/storage/save",
            json=[create_record_payload],
        )

        assert save_new_record_response.status_code == 200

        save_new_record_json = save_new_record_response.json()
        # Check that response contains the key of the new record
        assert isinstance(save_new_record_json, list)
        assert len(save_new_record_json) == 1
        assert save_new_record_json[0].get("Key") is not None
        assert save_new_record_json[0].get("Key") == "new_record"

        new_key = StubDataclassKey(id="new_record").build()
        new_record_in_db = DbContext.load_one(new_key, cast_to=StubDataclassDerived)
        records_count = len(list(DbContext.load_type(StubDataclassDerived)))

        assert new_record_in_db is not None
        assert new_record_in_db.id == "new_record"
        assert new_record_in_db.derived_str_field == "test"
        # DB should only contain the created record
        assert records_count == 1

        # Test updating existing record
        existing_record = StubDataclassDerived(id="existing_record", derived_str_field="old_value").build()
        DbContext.save_one(existing_record)

        update_record_response = test_client.post("/storage/save", json=[update_record_payload])

        assert update_record_response.status_code == 200

        update_record_json = update_record_response.json()
        # Check that response contains the key of the new record
        assert isinstance(update_record_json, list)
        assert len(update_record_json) == 1
        assert update_record_json[0].get("Key") is not None
        assert update_record_json[0].get("Key") == "existing_record"

        updated_record_in_db = DbContext.load_one(existing_record.get_key(), cast_to=StubDataclassDerived)
        records_count = len(list(DbContext.load_type(StubDataclassDerived)))
        assert updated_record_in_db is not None
        assert updated_record_in_db.id == "existing_record"
        assert updated_record_in_db.derived_str_field == "new_value"
        # DB should only contain the created record + the updated record
        assert records_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
