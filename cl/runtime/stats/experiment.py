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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.plots.plot import Plot
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.stats.experiment_condition import ExperimentCondition
from cl.runtime.stats.experiment_condition_key import ExperimentConditionKey
from cl.runtime.stats.experiment_key import ExperimentKey
from cl.runtime.stats.trial import Trial
from cl.runtime.stats.trial_key import TrialKey
from cl.runtime.stats.trial_query import TrialQuery
from cl.runtime.views.png_view import PngView


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin, ABC):
    """Abstract base class for a statistical experiment."""

    conditions: list[ExperimentConditionKey] = required()
    """Conditions for which the experiment is performed (optional)."""

    max_trials: int | None = None
    """Maximum number of trials to run per condition (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel across all conditions (optional, do not restrict if not set)."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.conditions is None:
            # Specify default condition if none are provided
            self.conditions = [ExperimentCondition(condition_id="Default").build()]
        if self.max_trials is not None and self.max_trials <= 0:
            raise RuntimeError(
                f"{typename(type(self))}.max_trials={self.max_trials} must be None or a positive number."
            )
        if self.max_parallel is not None and self.max_parallel <= 0:
            raise RuntimeError(
                f"{typename(type(self))}.max_parallel={self.max_parallel} must be None or a positive number."
            )

    @abstractmethod
    def create_trial(self, condition: ExperimentConditionKey) -> Trial:
        """
        Create and return a new trial record with actual and (if applicable) expected fields
        without checking if max_trials has already been reached.
        """

    def view_trials(self) -> tuple[TrialKey, ...]:
        """View trials of the experiment."""
        trial_query = TrialQuery(experiment=self.get_key()).build()
        trials = active(DataSource).load_by_query(trial_query, cast_to=Trial)
        trial_keys = [x.get_key() for x in trials]  # TODO: Use project_to instead of get_key
        return trial_keys

    @abstractmethod
    def get_plot(self, plot_id: str) -> Plot:
        """Get plot for the experiment."""

    def view_plot(self) -> PngView:
        return self.get_plot(self.experiment_id).get_view()

    def save_trial(self, condition: ExperimentConditionKey) -> None:
        """Create and save a new trial record without checking if max_trials has already been reached."""
        trial = self.create_trial(condition)
        active(DataSource).replace_one(trial, commit=True)

    def run_launch_one_trial(self) -> None:
        """Run one trial for each condition, error if max_trials is already reached or exceeded."""
        if self.max_parallel is not None and self.max_parallel != 1:
            raise RuntimeError(f"Parallel trial execution is not yet supported.")
        num_completed_trials = self.calc_num_completed_trials()
        if self.max_trials is not None and any(x >= self.max_trials for x in num_completed_trials):
            raise UserError(
                f"For at least one condition, the number of completed trials {max(num_completed_trials)}\n"
                f"has already reached or exceeded max_trials={self.max_trials}."
            )
        for condition in self.conditions:  # TODO: !! Make parallel
            # Run one additional trial for each condition
            self.save_trial(condition)

    def run_launch_many_trials(self, *, max_trials: int) -> None:
        """Run to reach the specified maximum number of trials for each condition."""
        if self.max_parallel is not None and self.max_parallel != 1:
            raise RuntimeError(f"Parallel trial execution is not yet supported.")
        num_additional_trials = self.calc_num_additional_trials(max_trials)
        for trial_idx in range(max(num_additional_trials)):
            for condition_idx, condition in enumerate(self.conditions):  # TODO: !! Make parallel
                # Run up to num_additional_trials for the current condition
                if trial_idx < num_additional_trials[condition_idx]:
                    self.save_trial(condition)

    def run_launch_all_trials(self) -> None:
        """Run trials until Experiment.max_trials is reached or exceeded."""
        if self.max_trials is None:
            raise RuntimeError("Experiment.run_all() requires Experiment.max_trials to be set.")
        self.run_launch_many_trials(max_trials=self.max_trials)

    def run_delete_completed_trials(self) -> None:
        """Delete completed trials for all conditions."""
        trial_query = TrialQuery(experiment=self.get_key()).build()
        active(DataSource).delete_by_query(trial_query)

    def calc_num_completed_trials(self) -> tuple[int, ...]:
        """
        Get the number of completed trials for each condition by running a query.

        Notes:
            Requires a DB query and may be slow, cache the result if possible.
        """
        trial_query = TrialQuery(experiment=self.get_key()).build()
        trials = active(DataSource).load_by_query(trial_query)  # TODO: Use project_to=Trial to reduce data transfer
        counts = tuple(sum(1 for t in trials if t.condition == c) for c in self.conditions)
        return counts

    def calc_num_additional_trials(self, max_trials: int) -> tuple[int, ...]:
        """
        Get the number of additional trials for each condition by running a query for the completed trials,
        error if max_trials is exceeded for any condition.

        Notes:
            Requires a DB query and may be slow, cache the result if possible.
        """
        if max_trials <= 0:
            raise RuntimeError(f"Parameter max_additional_trials={max_trials} must be a positive number.")
        if self.max_trials is not None and max_trials > self.max_trials:
            raise UserError(f"Parameter max_trials={max_trials} exceeds Experiment.max_trials={self.max_trials}.")

        # Check that max_trials is not exceeded
        num_completed_trials = self.calc_num_completed_trials()
        if any(x > max_trials for x in num_completed_trials):
            raise UserError(
                f"For at least one condition, the number of completed trials {max(num_completed_trials)}\n"
                f"exceeds max_trials={self.max_trials}."
            )

        # Because of the preceding check, the tuple will have non-negative elements
        num_additional_trials = tuple(max_trials - x for x in num_completed_trials)
        return num_additional_trials
