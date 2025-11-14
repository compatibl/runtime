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
from cl.runtime.params.param import Param
from cl.runtime.params.param_key import ParamKey
from cl.runtime.plots.plot import Plot
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_util import KeyUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.stat.binary_trial import BinaryTrial
from cl.runtime.stat.experiment_key import ExperimentKey
from cl.runtime.stat.trial import Trial
from cl.runtime.stat.trial_query import TrialQuery
from cl.runtime.views.png_view import PngView


@dataclass(slots=True, kw_only=True)
class Experiment(ExperimentKey, RecordMixin, ABC):
    """Abstract base class for a statistical experiment."""

    cases: list[ParamKey] = required()
    """Cases (conditions) for which the experiment is performed (optional)."""

    num_trials: int = required()
    """Number of trials to run per condition (optional)."""

    num_completed: float | None = None
    """Number of trials completed per condition (calculated, may be fractional)."""

    score: float | None = None
    """Score in percent (calculated)."""

    def get_key(self) -> ExperimentKey:
        return ExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.cases is None:
            # Specify default case if none are provided
            self.cases = [Param(param_id="Default").build()]  # TODO: !! Use a dedicated class DefaultCase

        if self.num_trials is None:
            raise RuntimeError(f"{typename(type(self))}.num_trials is None.")
        elif self.num_trials <= 0:
            raise RuntimeError(f"{typename(type(self))}.num_trials={self.num_trials} is not a positive number.")

    @abstractmethod
    def create_trial(self, condition: ParamKey) -> Trial:
        """
        Create and return a new trial record with actual and (if applicable) expected fields
        without checking if num_trials has already been reached.
        """

    @abstractmethod
    def get_plot(self, plot_id: str) -> Plot:
        """Get plot for the experiment."""

    def run_launch(self) -> None:
        """Run to reach the specified maximum number of trials for each condition."""

        # Retry running num_retries times
        num_retries = 3
        for _ in range(num_retries):
            num_additional_trials = self.calc_num_additional_trials()
            for trial_idx in range(max(num_additional_trials)):
                # Run trial for each case
                for case_idx, case in enumerate(self.cases):  # TODO: !! Make parallel
                    # Run up to num_additional_trials for the current condition
                    if trial_idx < num_additional_trials[case_idx]:
                        self.save_trial(case)

                # Calculate and save score to the experiment by querying trials
                self.run_score()

    def view_cases(self) -> tuple[ParamKey, ...]:
        """View cases of the experiment."""
        return tuple(self.cases)

    def view_trials(self) -> tuple[Trial, ...]:
        """View trials of the experiment."""
        trial_query = TrialQuery(experiment=self.get_key()).build()
        trials = active(DataSource).load_by_query(trial_query, cast_to=Trial)
        return trials

    def view_plot(self) -> PngView:
        return self.get_plot(self.experiment_id).get_view()

    def is_run(self) -> bool:
        """Return True if the record's dot-delimited ID ends with a timestamp."""
        tokens = self.experiment_id.split(".")
        if len(tokens) >= 2:
            # Dot delimited, check that the last token is a valid timestamp
            timestamp_token = tokens[-1]
            return Timestamp.guard_valid(timestamp_token, raise_on_fail=False)
        else:
            # Not dot delimited, cannot be a run
            return False

    def save_trial(self, condition: ParamKey) -> None:
        """Create and save a new trial record without checking if num_trials has already been reached."""
        trial = self.create_trial(condition)
        active(DataSource).replace_one(trial, commit=True)

    def run_score(self) -> None:
        """Save score to the experiment."""

        # TODO: Make abstract and implement for other experiment types
        # Update score by querying trials
        trials = self.view_trials()
        num_completed = len(trials) / len(self.cases)
        num_successes = sum(1 for trial in trials if isinstance(trial, BinaryTrial) and trial.outcome) / len(self.cases)
        score = 100 * float(num_successes) / float(num_completed) if num_completed > 0 else 0.0
        experiment = self.clone()
        experiment.num_completed = num_completed
        experiment.score = score
        active(DataSource).replace_one(experiment.build(), commit=True)

    def calc_num_completed_trials(self) -> tuple[int, ...]:
        """
        Get the number of completed trials for each condition by running a query.

        Notes:
            Requires a DB query and may be slow, cache the result if possible.
        """
        trial_query = TrialQuery(experiment=self.get_key()).build()
        trials = active(DataSource).load_by_query(trial_query)  # TODO: Use project_to=Trial to reduce data transfer
        counts = tuple(sum(1 for t in trials if KeyUtil.is_equal(t.param, c)) for c in self.cases)
        return counts

    def calc_num_additional_trials(self) -> tuple[int, ...]:
        """
        Get the number of additional trials for each condition by running a query for the completed trials,
        error if num_trials is exceeded for any condition.

        Notes:
            Requires a DB query and may be slow, cache the result if possible.
        """
        # Check that num_trials is not exceeded
        num_completed_trials = self.calc_num_completed_trials()
        if any(x > self.num_trials for x in num_completed_trials):
            raise UserError(
                f"For at least one condition, the number of completed trials {max(num_completed_trials)}\n"
                f"exceeds num_trials={self.num_trials}."
            )

        # Because of the preceding check, the tuple will have non-negative elements
        num_additional_trials = tuple(self.num_trials - x for x in num_completed_trials)
        return num_additional_trials
