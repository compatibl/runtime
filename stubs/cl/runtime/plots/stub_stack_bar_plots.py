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

from cl.runtime.plots.plot import Plot
from cl.runtime.plots.stack_bar_plot import StackBarPlot


class StubStackBarPlots:
    """Create GroupBarPlot stubs."""

    @classmethod
    def get_single_stack_plot(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with one group."""
        result = StackBarPlot(plot_id=plot_id)
        result.group_labels = ["Single Stack"] * 2
        result.bar_labels = ["Bar 1", "Bar 2"]
        result.values = [85.5, 92]
        return result.build()

    @classmethod
    def get_4_stacks_2_bars_plot(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with 4 groups and 2 bars."""
        num_groups = 4
        num_bars = 2

        bar_labels = []

        for i in range(num_bars):
            bar_labels += [f"Metric {i + 1}"] * num_groups

        group_labels = [f"Model {i + 1}" for i in range(num_groups)] * num_bars

        result = StackBarPlot(plot_id=plot_id)
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
    def get_4_stacks_5_bars(cls, plot_id: str) -> Plot:
        """Get GroupBarPlot plot with 4 groups and 5 bars."""
        num_groups = 4
        num_bars = 5

        bar_labels = []

        for i in range(num_bars):
            bar_labels += [f"Metric {i + 1}"] * num_groups

        group_labels = [f"Model {i + 1}" for i in range(num_groups)] * num_bars

        result = StackBarPlot(plot_id=plot_id)
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
        return result.build()
