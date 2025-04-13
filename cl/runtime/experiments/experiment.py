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
from itertools import count

from more_itertools import consume

from cl.runtime.contexts.db_context import DbContext
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.trial import Trial
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin[ExperimentKey], ABC):
    """Run and analyze the results of multiple trials."""

    supervised: bool = required()
    """True if the experiment is supervised (expected results are provided)."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, defaults to not running in parallel)."""

    result_type: str | None = None
    """Type name of the result (e.g., 'bool' for binary experiments), 'str' by default."""

    result_serializer: str | None = None
    """Serializer for the result, used only if the type is not str."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_id=self.experiment_id).build()

    @abstractmethod
    def run_one(self) -> None:
        """Run one trial."""

    def run_many(self, *, num_trials: int) -> None:
        """Run the specified number of trials, error if the total after the run will exceed max_trials."""

        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            num_remaining = self.get_num_remaining(num_trials=num_trials)
            consume(self.run_one() for _ in range(num_remaining))
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def run_all(self) -> None:
        """Run trials until the specified total number (max_trials) is reached."""

        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            num_remaining = self.get_num_remaining()
            consume(self.run_one() for _ in range(num_remaining))
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def get_num_remaining(self, *, num_trials: int | None = None) -> int:
        """Get the remaining number of trials to run, given the current number of completed trials."""

        if self.max_trials is None:
            if num_trials is not None:
                return num_trials
            else:
                raise RuntimeError(f"Cannot run all trials for experiment {self.experiment_id}\n"
                                   f"because max_trials is not set.")
        else:
            # TODO: !! Implement DbContext.count method
            # Load trials for this experiment
            # TODO: Support key filter fields trial_filter = Trial(experiment=self.get_key())
            trial_keys = tuple(DbContext.load_all(Trial))
            experiment_key = self.get_key()
            num_existing = len(tuple(x for x in trial_keys if x.experiment == experiment_key))

            if num_existing < self.max_trials:
                # The result does not exceed num_trials if specified
                if num_trials is not None:
                    return min(num_trials, self.max_trials - num_existing)
                else:
                    return self.max_trials - num_existing
            elif num_existing == self.max_trials:
                raise RuntimeError(
                    f"Cannot run more trials for experiment {self.experiment_id} because\n"
                    f"the maximum number of trials is {self.max_trials} has been reached."
                )
            else:
                raise RuntimeError(
                    f"Cannot run more trials for experiment {self.experiment_id} because\n"
                    f"the maximum number of trials is {self.max_trials} has been exceeded.\n"
                    f"Current number of trials is {num_existing} > {self.max_trials}."
                )

    def check_remaining(self) -> None:
        """Error message if the maximum number of trials has been reached."""
        # This call will raise an error if the maximum number of trials has been reached
        self.get_num_remaining()
