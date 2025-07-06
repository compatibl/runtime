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
import uuid
from typing import Iterator
from unittest import mock
from _pytest.fixtures import FixtureRequest
from bson import UUID_SUBTYPE
from bson import Binary
from cl.runtime import Db
from cl.runtime import SqliteDb
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.db.mongo.basic_mongo_mock_db import BasicMongoMockDb
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.tasks.celery.celery_queue import celery_delete_existing_tasks
from cl.runtime.tasks.celery.celery_queue import celery_start_queue


@pytest.fixture(scope="function")
def pytest_work_dir(request: FixtureRequest) -> Iterator[str]:
    """Pytest module fixture to make test module directory the local directory during test execution."""

    work_dir = PytestUtil.get_test_dir(request)

    # Change test working directory, create if does not exist
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    os.chdir(work_dir)

    # Back to the test
    yield work_dir

    # Change directory back before exiting the text
    os.chdir(request.config.invocation_dir)  # noqa


def _pytest_db(request: FixtureRequest, *, db_type: type | None = None) -> Iterator[Db]:
    """Setup and teardown a temporary databases in DB of the specified type."""

    # Set test DB name to test name in dot-delimited snake_case format, prefixed by 'temp_'
    test_name = PytestUtil.get_test_name(request)

    # Replace dots by underscores and add temp_ prefix
    normalized_test_name = test_name.replace(".", "_")
    db_id = f"temp_{normalized_test_name}"

    # Create a new DB instance of the specified type (use the type from settings if None)
    db = Db.create(db_type=db_type, db_id=db_id)

    # Delete all existing records in test DB before the test in case it was not performed by the preceding run
    db.drop_temp_db()

    # Run with the created DB, return db from the fixture
    with DbContext(db=db).build():
        yield db

    # Delete all existing records in test DB after the test
    db.drop_temp_db()


def convert_uuid_to_binary(uuid_: uuid.UUID, uuid_representation=None):
    """Convert a UUID to BSON Binary object."""
    return Binary(uuid_.bytes, UUID_SUBTYPE)


@pytest.fixture(scope="function")
def patch_uuid_conversion(request):
    """
    Fixture to patch the Binary.from_uuid method if request.param is None or BasicMongoMockDb.
    Required for tests with mongomock.
    """
    if (request_param := getattr(request, "param", None)) is None or request_param == BasicMongoMockDb:
        # The mongomock client does not convert UUID objects by default, but the real pymongo client does.
        with mock.patch("bson.binary.Binary.from_uuid", side_effect=convert_uuid_to_binary):
            yield
    else:
        yield


@pytest.fixture(scope="function")
def pytest_default_db(request: FixtureRequest) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using default DB."""
    yield from _pytest_db(request)


@pytest.fixture(scope="function")
def pytest_sqlite_db(request: FixtureRequest) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using SqliteDB."""
    yield from _pytest_db(request, db_type=BasicMongoMockDb)


@pytest.fixture(scope="function")
def pytest_basic_mongo_db(request: FixtureRequest) -> Iterator[Db]:
    """
    Pytest module fixture to setup and teardown temporary databases using BasicMongoDb.

    Notes:
        This requires a running MongoDB server with DB create and drop permissions.
        If this is not available, use pytest_basic_mongo_mock_db instead.
    """
    yield from _pytest_db(request, db_type=BasicMongoDb)


@pytest.fixture(scope="function")
def pytest_basic_mongo_mock_db(request: FixtureRequest, patch_uuid_conversion) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using BasicMongoMockDb."""
    yield from _pytest_db(request, db_type=BasicMongoMockDb)


@pytest.fixture(scope="function", params=[SqliteDb, BasicMongoMockDb])
def pytest_multi_db(request, patch_uuid_conversion) -> Iterator[Db]:
    """
    Pytest module fixture to setup and teardown temporary databases of all types
    that do not require a running server.
    """
    yield from _pytest_db(request, db_type=request.param)


@pytest.fixture(scope="session")  # TODO: Use a named celery queue for each test
def pytest_celery_queue():
    """Pytest session fixture to start Celery test queue for test execution."""
    print("Starting celery workers, will delete the existing tasks.")
    celery_delete_existing_tasks()
    celery_start_queue()  # TODO: Make test celery a separate queue
    yield
    celery_delete_existing_tasks()
    print("Stopping celery workers and cleaning up tasks.")
