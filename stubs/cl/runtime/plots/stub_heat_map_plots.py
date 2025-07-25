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

from cl.runtime.plots.heat_map_plot import HeatMapPlot
from cl.runtime.plots.plot import Plot

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


class StubHeatMapPlots:
    """Create HeatMapPlot stubs."""

    @classmethod
    def get_basic_plot(cls, plot_id: str) -> Plot:
        """Get basic plot."""

        row_labels = []

        for i in range(METRIC_COUNT):
            row_labels += [f"Metric {i + 1}"] * MODEL_COUNT

        col_labels = [f"Model {i + 1}" for i in range(MODEL_COUNT)] * METRIC_COUNT

        result = HeatMapPlot(plot_id=plot_id)
        result.title = "Model Comparison"
        result.row_labels = row_labels
        result.col_labels = col_labels
        result.received_values = [float(x) for x in _RECEIVED_VALUES]  # TODO: Remove when the conversion is automatic
        result.expected_values = [float(x) for x in _EXPECTED_VALUES]  # TODO: Remove when the conversion is automatic
        result.x_label = "Models"
        result.y_label = "Metrics"

        return result.build()
