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

from cl.runtime.plots.group_bar_plot import GroupBarPlot
from cl.runtime.plots.plot import Plot
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa

METRIC_COUNT = 5
"""Number of metrics."""

MODEL_COUNT = 4
"""Number of models."""

_EXPECTED_VALUES = [
    85.5,
    92,
    70,
    83.7,  # "Metric 1"
    89,
    95.3,
    77,
    95,  # "Metric 2"
    81,
    93.6,
    75,
    63.5,  # "Metric 3"
    85.5,
    98.8,
    78,
    83.7,  # "Metric 4"
    79.5,
    90,
    72.4,
    81.8,  # "Metric 5"
]
"""Expected values."""

_RECEIVED_VALUES = [
    85.5,
    94.5,
    70.5,
    85.2,  # "Metric 1"
    77,
    95.3,
    80.4,
    75,  # "Metric 2"
    60,
    98,
    75,
    78.5,  # "Metric 3"
    86,
    95,
    75,
    60,  # "Metric 4"
    77.3,
    92,
    76,
    74,  # "Metric 5"
]
"""Received values."""


class StubGroupBarPlots:
    """Create GroupBarPlot stubs."""

    @classmethod
    def get_single_group_plot(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with one group."""
        result = GroupBarPlot(plot_id=plot_id)
        result.group_labels = ["Single Group"] * 2
        result.bar_labels = ["Bar 1", "Bar 2"]
        result.values = [85.5, 92]
        return result.build()

    @classmethod
    def get_4_groups_2_bars_plot(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with 4 groups and 2 bars."""
        num_groups = 4
        num_bars = 2

        bar_labels = []

        for i in range(num_bars):
            bar_labels += [f"Metric {i + 1}"] * num_groups

        group_labels = [f"Model {i + 1}" for i in range(num_groups)] * num_bars

        result = GroupBarPlot(plot_id=plot_id)
        result.title = "Model Comparison"
        result.bar_labels = bar_labels
        result.group_labels = group_labels
        result.values = [
            10,
            20,
            20,
            40,  # "Metric 1"
            20,
            30,
            25,
            30,  # "Metric 2"
        ]
        return result.build()

    @classmethod
    def get_4_groups_5_bars(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with 4 groups and 5 bars."""
        num_groups = 4
        num_bars = 5

        bar_labels = []

        for i in range(num_bars):
            bar_labels += [f"Metric {i + 1}"] * num_groups

        group_labels = [f"Model {i + 1}" for i in range(num_groups)] * num_bars

        result = GroupBarPlot(plot_id=plot_id)
        result.title = "Model Comparison"
        result.bar_axis_label = "Metrics"
        result.value_axis_label = "Models"
        result.bar_labels = bar_labels
        result.group_labels = group_labels
        result.values = [
            85.5,
            92,
            70,
            83.7,  # "Metric 1"
            89,
            95.3,
            77,
            95,  # "Metric 2"
            81,
            93.6,
            75,
            63.5,  # "Metric 3"
            85.5,
            98.8,
            78,
            83.7,  # "Metric 4"
            79.5,
            90,
            72.4,
            81.8,  # "Metric 5"
        ]
        result.value_ticks = list(range(0, 101, 10))
        return result.build()
