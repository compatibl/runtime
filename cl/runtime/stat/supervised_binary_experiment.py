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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.plots.stack_bar_plot import StackBarPlot
from cl.runtime.records.key_util import KeyUtil
from cl.runtime.stat.binary_experiment import BinaryExperiment
from cl.runtime.params.param import Param
from cl.runtime.stat.supervised_binary_trial import SupervisedBinaryTrial
from cl.runtime.stat.trial_query import TrialQuery


@dataclass(slots=True, kw_only=True)
class SupervisedBinaryExperiment(BinaryExperiment, ABC):
    """Supervised binary experiment with boolean actual and expected result types."""

    def get_plot(self, plot_id: str) -> StackBarPlot:
        """Builds and returns plot for Supervised Binary Experiment."""
        if not self.conditions:
            raise RuntimeError(
                "Experiment must have one or more condition to build a plot."
            )  # TODO: Support no conditions

        group_labels = []
        bar_labels = []
        values = []

        # Get trials for all conditions
        trial_query = TrialQuery(experiment=self.get_key()).build()
        all_trials = active(DataSource).load_by_query(trial_query, cast_to=SupervisedBinaryTrial)

        conditions = active(DataSource).load_many(self.conditions, cast_to=Param)
        for condition in conditions:
            # Get trials for the condition
            trials = tuple(trial for trial in all_trials if KeyUtil.is_equal(trial.condition, condition))
            total = len(trials)

            tp = tn = fp = fn = 0

            for trial in trials:
                if trial.outcome and trial.expected_outcome:
                    tp += 1
                elif not trial.outcome and not trial.expected_outcome:
                    tn += 1
                elif trial.outcome and not trial.expected_outcome:
                    fp += 1
                elif not trial.outcome and trial.expected_outcome:
                    fn += 1

            group_labels.extend([condition.label] * 4)
            bar_labels.extend(["TP", "TN", "FP", "FN"])
            values.extend(
                [
                    tp / total,
                    tn / total,
                    fp / total,
                    fn / total,
                ]
            )

        result = StackBarPlot(
            plot_id=plot_id,
            title="Classification Outcome Ratios by Scenario",
            value_axis_label="Ratio",
            xtick_rotation=45,
            xtick_ha="right",
            value_ticks=[0.0, 0.5, 1.0],
        )
        result.group_labels = group_labels
        result.bar_labels = bar_labels

        result.values = values
        return result.build()
