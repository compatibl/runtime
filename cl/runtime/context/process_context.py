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

from cl.runtime.context.context import Context
from cl.runtime.log.log import Log
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.settings import is_inside_test
from cl.runtime.storage.dataset_util import DatasetUtil
from cl.runtime.testing.unit_test_context import UnitTestContext
from cl.runtime.testing.unit_test_util import UnitTestUtil
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class ProcessContext(Context):
    """Context for a standalone process."""

    def __post_init__(self):
        """Configure context."""

        # Check we are not inside a test
        if is_inside_test:
            raise RuntimeError(f"'{type(self).__name__}' is used inside a test, "
                               f"use '{UnitTestContext.__name__}' instead.")

        # Get context settings
        context_settings = ContextSettings.instance()

        # Use data_source_id from settings for context_id
        self.context_id = context_settings.data_source_id

        # Create the log class specified in settings
        log_type = ClassInfo.get_class_type(context_settings.log_class)
        self.log = log_type(log_id=self.context_id)

        # Create the data source class specified in settings
        data_source_type = ClassInfo.get_class_type(context_settings.data_source_class)
        self.data_source = data_source_type(data_source_id=self.context_id)

        # Root dataset
        self.dataset = DatasetUtil.root()