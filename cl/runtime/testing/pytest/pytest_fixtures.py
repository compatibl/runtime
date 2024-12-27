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
from typing import Iterator
from typing import Type
from _pytest.fixtures import FixtureRequest
from cl.runtime import ClassInfo
from cl.runtime import Db
from cl.runtime.context.db_context import DbContext
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.tasks.celery.celery_queue import celery_delete_existing_tasks
from cl.runtime.tasks.celery.celery_queue import celery_start_queue
from cl.runtime.testing.pytest.pytest_util import PytestUtil


def _create_db(request: FixtureRequest, db_type: Type | None = None):
    """Create DB of the specified type, or use DB type from context settings if not specified."""

    # Get DB type from context settings if not specified
    if db_type is None:
        context_settings = ContextSettings.instance()
        db_type = ClassInfo.get_class_type(context_settings.db_class)

    # Get test DB identifier
    env_name = PytestUtil.get_env_name(request)
    db_id = "temp;" + env_name.replace(".", ";")

    # Create and return a new DB instance
    result = db_type(db_id=db_id)
    return result


@pytest.fixture(scope="function")
def testing_work_dir(request: FixtureRequest) -> Iterator[str]:
    """Pytest module fixture to make test module directory the local directory during test execution."""

    work_dir = PytestUtil.get_env_dir(request)

    # Change test working directory, create if does not exist
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    os.chdir(work_dir)

    # Back to the test
    yield work_dir

    # Change directory back before exiting the text
    os.chdir(request.config.invocation_dir)


@pytest.fixture(scope="function")
def testing_db(request) -> Iterator[Db]:
    """Pytest module fixture to setup and teardown a temporary test DB."""

    # Create test DB
    db = _create_db(request)

    # Run with the created DB, return db from the fixture
    with DbContext(db=db):
        yield db

    # Change directory back before exiting the text
    os.chdir(request.config.invocation_dir)


@pytest.fixture(scope="session")  # TODO: Use a named celery queue for each test
def testing_celery_queue():
    """Pytest session fixture to start Celery test queue for test execution."""
    print("Starting celery workers, will delete the existing tasks.")
    celery_delete_existing_tasks()
    celery_start_queue()  # TODO: Make test celery a separate queue
    yield
    celery_delete_existing_tasks()
    print("Stopping celery workers and cleaning up tasks.")
