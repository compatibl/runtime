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

from dataclasses import dataclass
from cl.runtime.plots.plot import Plot
from cl.runtime.plots.scatter_values_2d import ScatterValues2D
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class ScatterPlot2D(Plot):
    """2D scatter plot with markers and surfaces."""

    data: list[ScatterValues2D] = required()
    """List of values objects, each containing data and style settings."""

    x_label: str | None = None
    """X-axis label."""

    y_label: str | None = None
    """Y-axis label."""

    x_lim: tuple[float, ...] | None = None
    """Y-axis limits (optional)."""

    y_lim: tuple[float, ...] | None = None
    """Y-axis limits (optional)."""
