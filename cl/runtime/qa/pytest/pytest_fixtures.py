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
import logging.config
import os
import uuid
from typing import Iterator
from unittest import mock
from _pytest.fixtures import FixtureRequest
from bson import UUID_SUBTYPE
from bson import Binary
from cl.runtime.contexts.context_manager import activate
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.db import Db
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.db.mongo.basic_mongo_mock_db import BasicMongoMockDb
from cl.runtime.db.sql.sqlite_db import SqliteDb
from cl.runtime.log.log_config import logging_config
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.server.env import Env
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.tasks.celery.celery_queue import celery_app
from cl.runtime.tasks.celery.celery_queue import celery_delete_existing_tasks


def _db_fixture(request: FixtureRequest, *, db_type: type | None = None) -> Iterator[Db]:
    """Setup and teardown a temporary databases in DB of the specified type."""

    # Set test DB name to test name in dot-delimited snake_case format, prefixed by 'temp_'
    test_name = PytestUtil.get_test_path_from_request(request, name_only=True)

    # Activate test environment
    with activate(
        Env(
            env_id=test_name,
            env_kind=EnvKind.TEST,
            env_dir=PytestUtil.get_test_path_from_request(request, name_only=False),
        ).build()
    ):

        # Replace dots by semicolons
        db_id = test_name.replace(".", ";")

        # Create a new DB instance of the specified type (use the type from settings if None)
        db = Db.create(db_type=db_type, db_id=db_id)

        # Delete all existing records in unit test DB before the test in case it was not performed by the preceding run
        db.drop_test_db()

        # Run with the created DB, return db from the fixture
        with activate(DataSource(db=db).build()):
            yield db

        # Delete all existing records in unit test DB after the test
        db.drop_test_db()


@pytest.fixture(scope="function")
def default_db_fixture(request: FixtureRequest) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using default DB."""

    # Get default Db type from settings
    db_settings = DbSettings.instance()
    default_db_type = TypeInfo.from_type_name(db_settings.db_type)

    if default_db_type is BasicMongoMockDb:
        # Patch 'from_uuid' method if db type is BasicMongoMockDb
        with mock.patch("bson.binary.Binary.from_uuid", side_effect=convert_uuid_to_binary):
            yield from _db_fixture(request, db_type=default_db_type)
    else:
        yield from _db_fixture(request, db_type=default_db_type)


@pytest.fixture(scope="function")
def sqlite_db_fixture(request: FixtureRequest) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using SqliteDB."""
    yield from _db_fixture(request, db_type=SqliteDb)


@pytest.fixture(scope="function")
def basic_mongo_db_fixture(request: FixtureRequest) -> Iterator[Db]:
    """
    Pytest module fixture to setup and teardown temporary databases using BasicMongoDb.

    Notes:
        This requires a running MongoDB server with DB create and drop permissions.
        If this is not available, use basic_mongo_mock_db_fixture instead.
    """
    yield from _db_fixture(request, db_type=BasicMongoDb)


@pytest.fixture(scope="function")
def basic_mongo_mock_db_fixture(request: FixtureRequest) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown temporary databases using BasicMongoMockDb."""
    # Patch 'from_uuid' method
    with mock.patch("bson.binary.Binary.from_uuid", side_effect=convert_uuid_to_binary):
        yield from _db_fixture(request, db_type=BasicMongoMockDb)


@pytest.fixture(scope="function", params=[SqliteDb, BasicMongoMockDb])  # TODO: Load the list from settings instead
def multi_db_fixture(request) -> Iterator[Db]:
    """
    Pytest module fixture to setup and teardown temporary databases of all types
    that do not require a running server.
    """
    # Patch 'from_uuid' method if db type is BasicMongoMockDb
    if request.param is BasicMongoMockDb:
        with mock.patch("bson.binary.Binary.from_uuid", side_effect=convert_uuid_to_binary):
            yield from _db_fixture(request, db_type=request.param)
    else:
        yield from _db_fixture(request, db_type=request.param)


@pytest.fixture(scope="session")  # TODO: Use a named celery queue for each test
def celery_queue_fixture():
    """Pytest session fixture to start Celery test queue for test execution."""
    print("Starting celery workers, will delete the existing tasks.")
    celery_delete_existing_tasks()

    # Here we configure Celery to run in "eager mode":
    # tasks are executed right away in the current process,
    # without starting a worker or using the broker.
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

    yield
    celery_delete_existing_tasks()
    print("Stopping celery workers and cleaning up tasks.")


@pytest.fixture(scope="function")
def work_dir_fixture(request: FixtureRequest) -> Iterator[str]:
    """Pytest module fixture to make test module directory the local directory during test execution."""

    work_dir = PytestUtil.get_test_path_from_request(request, name_only=False)

    # Change test working directory, create if does not exist
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    os.chdir(work_dir)

    # Back to the test
    yield work_dir

    # Change directory back before exiting the text
    os.chdir(request.config.invocation_dir)  # noqa


def convert_uuid_to_binary(uuid_: uuid.UUID, uuid_representation=None):
    """Convert a UUID to BSON Binary object."""
    return Binary(uuid_.bytes, UUID_SUBTYPE)


@pytest.fixture(scope="session", autouse=True)
def configure_logging_fixture(request: FixtureRequest):
    """Configure logging with basic config."""
    logging.config.dictConfig(logging_config)
