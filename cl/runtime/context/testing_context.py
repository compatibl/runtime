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
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class TestingContext(Context):
    """
    Utilities for both pytest and unittest.

    Notes:
        - The name TestingContext was selected to avoid Test prefix and does not indicate it is for a specific package
        - This module not itself import pytest or unittest package
    """

    def __post_init__(self):
        """Configure fields that were not specified in constructor."""

        # Do not execute this code on frozen or deserialized context instances
        #   - If the instance is frozen, init_all has already been executed
        #   - If the instance is deserialized, init_all has been executed before serialization
        if not self.is_deserialized:

            # Confirm we are inside a test, error otherwise
            if not Settings.is_inside_test:
                raise RuntimeError(f"TestingContext created outside a test.")

            # Get test name in 'module.test_function' or 'module.TestClass.test_method' format inside a test
            context_settings = ContextSettings.instance()

            # For a test, env name is dot-delimited test module, class in snake_case (if any), and method or function
            env_name = EnvUtil.get_env_name()

            # Use test name in dot-delimited format for context_id unless specified by the caller
            if self.context_id is None:
                self.context_id = env_name

            # Set user from OS if not specified directly
            if self.user is None:
                # Set user to env name for unit testing
                self.user = UserKey(username=env_name)

        # Return self to enable method chaining
        return self

