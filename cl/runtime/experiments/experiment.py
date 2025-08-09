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
from abc import abstractmethod
from dataclasses import dataclass
from typing import List
from typing import Sequence
from typing import TypeVar
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.experiment_scenario_key import ExperimentScenarioKey
from cl.runtime.experiments.trial import Trial
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.experiments.trial_key_query import TrialKeyQuery
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.plots.plot import Plot
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.views.png_view import PngView

TTrial = TypeVar("TTrial", bound=Trial)


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin, ABC):
    """Abstract base class for a statistical experiment."""

    scenarios: List[ExperimentScenarioKey] | None = None
    """Experiment scenarios (optional)."""

    max_trials: int | None = None
    """Maximum number of trials to run per scenario (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, do not restrict if not set)."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_kind=self.experiment_kind, experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.max_trials is not None and self.max_trials <= 0:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.max_trials={self.max_trials}. It must be None or a positive number."
            )
        if self.max_parallel is not None and self.max_parallel <= 0:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.max_parallel={self.max_parallel}. It must be None or a positive number."
            )

    @abstractmethod
    def create_trial(self, scenario: ExperimentScenarioKey) -> Trial:
        """
        Create and return a new trial record with actual and (if applicable) expected fields
        without checking if max_trials has already been reached.
        """

    def view_trials(self) -> Sequence[TrialKey]:
        """View trials of the experiment."""
        trial_key_query = TrialKeyQuery(experiment=self.get_key()).build()
        trials = active(DataSource).load_where(trial_key_query, cast_to=Trial)
        trial_keys = [x.get_key() for x in trials]  # TODO: Use project_to instead of get_key
        return trial_keys

    @abstractmethod
    def get_plot(self, plot_id: str) -> Plot:
        """Get plot for the experiment."""

    def view_plot(self) -> PngView:
        return self.get_plot(self.experiment_id).get_view()

    def save_trial(self, scenario: ExperimentScenarioKey) -> None:
        """Create and save a new trial record without checking if max_trials has already been reached."""
        trial = self.create_trial(scenario)
        active(DataSource).save_one(trial)

    def run_one(self) -> None:
        """Run one trial, error if max_trials is already reached or exceeded."""
        # This will raise an error if the maximum number of trials has been reached
        self._query_remaining_trials_and_check_limit()
        # Create and save one trial
        for scenario in self.scenarios:
            self.save_trial(scenario)

    def run_many(self, *, num_trials: int) -> None:
        """Run up to the specified number of trials, stop when max_trials is reached or exceeded."""

        # This will raise an error if the maximum number of trials has been reached
        num_remaining = self._query_remaining_trials_and_check_limit(num_trials=num_trials)

        # Create and save up to num_trials but not exceeding max_trials if set
        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            for _ in range(num_remaining):
                for scenario in self.scenarios:
                    self.save_trial(scenario)
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def run_all(self) -> None:
        """Run trials until the specified total number (max_trials) is reached or exceeded."""

        # This will raise an error if the maximum number of trials has been reached
        if (num_remaining := self._query_remaining_trials_and_check_limit()) is None:
            raise UserError(
                f"Cannot invoke run_all for experiment {self.experiment_id}\n"
                f"because max_trials is not set, use run_one or run_many instead."
            )

        if self.max_parallel is None or self.max_parallel <= 1:
            # Run sequentially
            for _ in range(num_remaining):
                for scenario in self.scenarios:
                    self.save_trial(scenario)
        else:
            # TODO: Implement parallel execution of trials
            raise RuntimeError(f"Cannot run trials in parallel for experiment {self.experiment_id}.")

    def query_existing_trials(self) -> int:
        """Get the remaining of existing trials."""
        trial_key_query = TrialKeyQuery(experiment=self.get_key()).build()
        num_existing_trials = active(DataSource).count_where(trial_key_query)
        return num_existing_trials

    def query_remaining_trials(self, *, num_trials: int | None = None) -> int | None:
        """
        Get the remaining number of trials to run, given the current number of completed trials.

        Notes:
            - Requires a DB query and may be slow, cache the result if possible
            - Returns None if both max_trials and num_trials are None.
        """

        if num_trials is not None and num_trials <= 0:
            raise RuntimeError(f"Parameter num_trials={num_trials} must be None or a positive number.")

        if self.max_trials is None:
            if num_trials is not None:
                return num_trials
            else:
                # Return None if both max_trials and num_trials are None
                return None
        else:
            if (num_existing_trials := self.query_existing_trials()) < self.max_trials:
                if num_trials is not None:
                    # The result does not exceed num_trials if specified,
                    return min(self.max_trials - num_existing_trials, num_trials)
                else:
                    return self.max_trials - num_existing_trials
            else:
                # The maximum number of trials has been reached or exceeded, return 0
                return 0

    def _query_remaining_trials_and_check_limit(self, *, num_trials: int | None = None) -> int:
        """
        Error message if the maximum number of trials has been reached or exceeded, otherwise the number
        of remaining trials to run, given the current number of completed trials.

        Notes:
            - Requires a DB query and may be slow, cache the result if possible
            - Returns None if both max_trials and num_trials are None.
        """
        result = self.query_remaining_trials(num_trials=num_trials)
        if result == 0:
            raise RuntimeError(
                f"The maximum number of trials ({self.max_trials}) has already been reached\n"
                f"for {TypeUtil.name(self)} with experiment_id={self.experiment_id}."
            )
        return result

    def get_scenario_trials(self, all_trials: Sequence[TTrial], scenario: ExperimentScenarioKey) -> tuple[TTrial, ...]:
        """Get trials of the particular scenario from all trials."""
        trials = tuple(trial for trial in all_trials if trial.scenario == scenario)
        if not trials:
            raise RuntimeError(
                f"No trials for experiment {self.experiment_id} and scenario {scenario.experiment_scenario_id}."
            )
        return trials
