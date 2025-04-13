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
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin[ExperimentKey], ABC):
    """Run and analyze the results of multiple trials."""

    supervised: bool = required()
    """True if the experiment is supervised (expected results are provided)."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, do not restrict if not set)."""

    result_type: str | None = None
    """Type name of the result (e.g., 'bool' for binary experiments), 'str' by default."""

    result_serializer: str | None = None
    """Serializer for the result, used only if the type is not str."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.max_trials is not None and self.max_trials <= 0:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.max_trials={self.max_trials}. It must be None or a positive number.")
        if self.max_parallel is not None and self.max_parallel <= 0:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.max_parallel={self.max_parallel}. It must be None or a positive number.")

    @abstractmethod
    def run_one(self) -> None:
        """Run one trial, error message if max_trials is already reached or exceeded."""

    def run_many(self, *, num_trials: int) -> None:
        """Run up to the specified number of trials, stop when max_trials is reached or exceeded."""

        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            num_remaining = self.count_remaining_trials(num_trials=num_trials)
            consume(self.run_one() for _ in range(num_remaining))
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def run_all(self) -> None:
        """Run trials until the specified total number (max_trials) is reached or exceeded."""

        if (num_remaining := self.count_remaining_trials()) is None:
            raise RuntimeError(f"Cannot invoke run_all for experiment {self.experiment_id}\n"
                               f"because max_trials is not set, use run_one or run_many instead.")

        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            consume(self.run_one() for _ in range(num_remaining))
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def count_existing_trials(self) -> int:
        """Get the remaining of existing trials."""
        # TODO: !! Implement DbContext.count method
        # Load trials for this experiment
        # TODO: Support key filter fields trial_filter = Trial(experiment=self.get_key())
        trial_keys = tuple(DbContext.load_all(Trial))
        experiment_key = self.get_key()
        num_existing_trials = len(tuple(x for x in trial_keys if x.experiment == experiment_key))
        return num_existing_trials

    def count_remaining_trials(self, *, num_trials: int | None = None) -> int | None:
        """Get the remaining number of trials to run, given the current number of completed trials."""

        if num_trials is not None and num_trials <= 0:
            raise RuntimeError(f"Parameter num_trials={num_trials} must be None or a positive number.")

        if self.max_trials is None:
            if num_trials is not None:
                return num_trials
            else:
                # Return None if both max_trials and num_trials are None
                return None
        else:
            if (num_existing_trials := self.count_existing_trials()) < self.max_trials:
                if num_trials is not None:
                    # The result does not exceed num_trials if specified,
                    return min(self.max_trials - num_existing_trials, num_trials)
                else:
                    return self.max_trials - num_existing_trials
            else:
                # The maximum number of trials has been reached or exceeded
                return 0

    def check_remaining_trials(self) -> None:
        """Error message if the maximum number of trials has been reached."""
        # This call will raise an error if the maximum number of trials has been reached
        if self.max_trials is not None:
            num_existing_trials = self.count_existing_trials()
            if num_existing_trials == self.max_trials:
                raise RuntimeError(
                    f"Cannot run more trials for experiment {self.experiment_id} because\n"
                    f"the maximum number of trials is {self.max_trials} has been reached."
                )
            elif num_existing_trials > self.max_trials:
                    raise RuntimeError(
                        f"Cannot run more trials for experiment {self.experiment_id} because\n"
                        f"the maximum number of trials is {self.max_trials} has been exceeded.\n"
                        f"Number of existing trials: {num_existing_trials} > {self.max_trials}."
                    )
