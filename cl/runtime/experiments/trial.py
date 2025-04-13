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
from dataclasses import dataclass

from cl.runtime.contexts.db_context import DbContext
from cl.runtime.experiments.experiment import Experiment
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Trial(TrialKey, RecordMixin[TrialKey], ABC):
    """Result and supporting data for a single trial of an experiment."""

    experiment: ExperimentKey = required()
    """Experiment for which the trial is performed."""

    result: str = required()
    """Trial result serialized as YAML."""

    expected: str | None = None
    """Expected result serialized as YAML for supervised experiments only, None otherwise."""

    def get_key(self) -> TrialKey:
        return TrialKey(timestamp=self.timestamp).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Assign timestamp to the trial if not already set
        if self.timestamp is None:
            self.timestamp = Timestamp.create()

        # Load the experiment object
        experiment = DbContext.load_one(Experiment, self.experiment)

        # Validate the result based on the experiment.result_type and convert it to string

