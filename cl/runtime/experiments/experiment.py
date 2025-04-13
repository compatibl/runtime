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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin[ExperimentKey], ABC):
    """Run and analyze the results of multiple trials."""

    supervised: bool = required()
    """True if the experiment is supervised (expected results are provided)."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    result_type: str | None = None
    """Type name of the result (e.g., 'bool' for binary experiments), 'str' by default."""

    result_serializer: str | None = None
    """Serializer for the result, used only if the type is not str."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_id=self.experiment_id).build()

    @abstractmethod
    def run_one(self) -> None:
        """Run one trial."""

    def run_many(self, num_trials: int) -> None:
        """Run the specified number of trials, error if the total after the run will exceed max_trials."""

    def run_all(self) -> None:
        """Run trials until the specified total number (max_trials) is reached."""

