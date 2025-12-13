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
from collections import Counter
from dataclasses import dataclass
from typing import List
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.experiments.classifier_trial import ClassifierTrial
from cl.runtime.experiments.experiment import Experiment
from cl.runtime.experiments.trial_key_query import TrialKeyQuery
from cl.runtime.plots.stack_bar_plot import StackBarPlot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class ClassifierExperiment(Experiment, ABC):
    """Unsupervised classifier experiment with string result type representing the class label."""

    class_labels: list[str] = required()
    """List of permitted class labels."""

    def get_plot(self, plot_id: str) -> StackBarPlot:
        """Builds and returns plot for Classifier Experiment."""

        if not self.scenarios:
            raise RuntimeError("Experiment must have scenarios to build a plot.")

        group_labels = []
        bar_labels = []
        values = []

        scenario_counts = []
        trial_query = TrialKeyQuery(experiment=self.get_key()).build()
        all_trials = active(DataSource).load_where(trial_query, cast_to=ClassifierTrial)

        for scenario in self.scenarios:
            trials = self.get_scenario_trials(all_trials, scenario)
            total = len(trials)
            class_counts = Counter(trial.actual for trial in trials)
            scenario_counts.append((scenario.experiment_scenario_id, class_counts, total))

        for scenario_id, counts, total in scenario_counts:
            for class_label in self.class_labels:
                group_labels.append(scenario_id)
                bar_labels.append(class_label)
                values.append(counts.get(class_label, 0) / total)

        result = StackBarPlot(
            plot_id=plot_id,
            title="Proportions by Scenario and Class",
            value_axis_label="Proportion",
            xtick_rotation=45,
            xtick_ha="right",
            value_ticks=[0.0, 0.5, 1.0],
        )
        result.group_labels = group_labels
        result.bar_labels = bar_labels

        result.values = values
        return result.build()
