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

from abc import ABC
from typing import Generic
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.experiments.experiment_mixin import ExperimentMixin, TTrial
from cl.runtime.records.protocols import TKey


class BinaryExperimentMixin(Generic[TKey, TTrial], ExperimentMixin[TKey, TTrial], ABC):
    """Mixin class for an unsupervised statistical experiment where each trial has True or False outcome."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    def view_trials(self) -> TTrial:
        """View trials of the experiment."""
        # Get trial type at runtime
        trial_type = self.get_trial_type()
        # TODO: Use query
        all_trials = DbContext.load_all(trial_type)
        trials = [trial for trial in all_trials if trial.experiment.experiment_id == self.experiment_id]
        return trials
