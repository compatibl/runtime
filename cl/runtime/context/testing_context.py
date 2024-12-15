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
from typing import final

from typing_extensions import Self

from cl.runtime.backend.core.user_key import UserKey
from cl.runtime.context.context import Context
from cl.runtime.context.env_util import EnvUtil
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.settings import Settings


@final
@dataclass(slots=True, kw_only=True)
class TestingContext(Context):
    """
    Utilities for both pytest and unittest.

    Notes:
        - The name TestingContext was selected to avoid Test prefix and does not indicate it is for a specific package
        - This module not itself import pytest or unittest package
    """

    db_class: str | None = None  # TODO: Find another way to override to avoid duplication with db field
    """Override for the database class in module.ClassName format."""

    def __post_init__(self):
        """Set is_root=True before running init_all."""
        self.is_root = True

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        # Do not execute this code on frozen or deserialized context instances
        #   - If the instance is frozen, init_all has already been executed
        #   - If the instance is deserialized, init_all has been executed before serialization
        if not self.is_frozen() and not self.is_deserialized:
            # Confirm we are inside a test, error otherwise
            if not Settings.is_inside_test:
                raise RuntimeError(f"TestingContext created outside a test.")

            # Get test name in 'module.test_function' or 'module.TestClass.test_method' format inside a test
            context_settings = ContextSettings.instance()

            # For the test, env name is dot-delimited test module, class in snake_case (if any), and method or function
            env_name = EnvUtil.get_env_name()

            # Use test name in dot-delimited format for context_id unless specified by the caller
            if self.context_id is None:
                self.context_id = env_name

            # Set user from OS if not specified directly
            if self.user is None:
                # Set user to env name for unit testing
                self.user = UserKey(username=env_name)

            # Use log from settings if not specified directly
            if self.log is None:
                # TODO: Set log field here explicitly instead of relying on implicit detection of test environment
                log_type = ClassInfo.get_class_type(context_settings.log_class)
                self.log = log_type(log_id=self.context_id)

            # Use database class from settings if not specified directly
            if self.db is None:
                if self.db_class is not None:
                    db_class = self.db_class
                else:
                    db_class = context_settings.db_class

                # Use 'temp' followed by context_id converted to semicolon-delimited format for db_id
                db_id = "temp;" + self.context_id.replace(".", ";")

                # Instantiate a new database object for every test
                db_type = ClassInfo.get_class_type(db_class)
                self.db = db_type(db_id=db_id)

            # Use root dataset if not specified directly
            if self.dataset is None:
                self.dataset = DatasetUtil.root()

            # Set fields to their values in ContextSettings
            if self.experiment is None:
                if StringUtil.is_not_empty(experiment_id := ContextSettings.instance().experiment):
                    self.experiment = ExperimentKey(experiment_id=experiment_id)
            if self.trial is None:
                if StringUtil.is_not_empty(trial_id := ContextSettings.instance().trial):
                    self.trial = TrialKey(trial_id=trial_id)

        # Return self to enable method chaining
        return self

    def __enter__(self):
        """Supports 'with' operator for resource disposal."""

        # Call '__enter__' method of base first
        Context.__enter__(self)

        # Execute on root instances only if they are not deserialized (e.g. not the instances passed to a task queue)
        if self.db is not None and self.is_root and not self.is_deserialized:
            # Delete all existing data in temp database and drop DB in case it was not cleaned up
            # due to abnormal termination of the previous test run
            self.db.delete_all_and_drop_db()  # noqa

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Supports 'with' operator for resource disposal."""

        # Execute on root instances only if they are not deserialized (e.g. not the instances passed to a task queue)
        if self.db is not None and self.is_root and not self.is_deserialized:
            # Delete all data in temp database and drop DB to clean up
            self.db.delete_all_and_drop_db()  # noqa

        # Call '__exit__' method of base last
        return Context.__exit__(self, exc_type, exc_val, exc_tb)
