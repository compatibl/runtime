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
from getpass import getuser
from cl.convince.llms.llm_key import LlmKey
from cl.runtime.backend.core.user_key import UserKey
from cl.runtime.context.context import Context
from cl.runtime.context.testing_context import TestingContext
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class ProcessContext(Context):
    """Context for a standalone process."""

    def __post_init__(self):
        """Configure context."""

        # Do not execute this code on deserialized context instances (e.g. when they are passed to a task queue)
        if not self.is_deserialized:
            # Confirm we are not inside a test, error otherwise
            if Settings.is_inside_test:
                raise RuntimeError(
                    f"'{type(self).__name__}' is used inside a test, " f"use '{TestingContext.__name__}' instead."
                )

            # Get context settings
            context_settings = ContextSettings.instance()

            # Use db_id from settings for context_id unless specified by the caller
            if context_settings.context_id is not None:
                self.context_id = context_settings.context_id
            else:
                self.context_id = Settings.process_timestamp

            # Set user
            # TODO: Set in based on auth for enterprise cloud deployments
            # TODO: Use LastName, FirstName format for enterprise if possible
            self.user = UserKey(username=getuser())

            # Create the log class specified in settings
            log_type = ClassInfo.get_class_type(context_settings.log_class)
            self.log = log_type(log_id=self.context_id)

            # Create the database class specified in settings
            db_type = ClassInfo.get_class_type(context_settings.db_class)

            # Use context_id as db_id
            self.db = db_type(db_id=self.context_id)

            # Root dataset
            self.dataset = DatasetUtil.root()

            # Set fields to their values in ContextSettings
            if self.experiment is None:
                if StringUtil.is_not_empty(experiment_id := ContextSettings.instance().experiment):
                    self.experiment = ExperimentKey(experiment_id=experiment_id)
            if self.trial is None:
                if StringUtil.is_not_empty(trial_id := ContextSettings.instance().trial):
                    self.trial = TrialKey(trial_id=trial_id)
            if self.full_llm is None:
                if StringUtil.is_not_empty(full_llm_id := ContextSettings.instance().full_llm):
                    self.full_llm = LlmKey(llm_id=full_llm_id)
            if self.mini_llm is None:
                if StringUtil.is_not_empty(mini_llm_id := ContextSettings.instance().mini_llm):
                    self.mini_llm = LlmKey(llm_id=mini_llm_id)
