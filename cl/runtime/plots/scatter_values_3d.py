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
import numpy as np

from cl.runtime.plots.plot import Plot
from cl.runtime.plots.plot_color import PlotColor
from cl.runtime.plots.plot_line_style import PlotLineStyle
from cl.runtime.plots.plot_marker_style import PlotMarkerStyle
from cl.runtime.plots.plot_surface_style import PlotSurfaceStyle
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class ScatterValues3D(DataclassMixin):
    """Scatter data for a single set of points in 3D plot."""

    x: list[float] = required()
    """List of X-coordinates."""

    y: list[float] = required()
    """List of Y-coordinates."""

    z: list[float] = required()
    """List of Z-coordinates."""

    color: PlotColor | None = None
    """Marker and surface color."""

    marker_style: PlotMarkerStyle | None = None
    """Marker style."""

    surface_style: PlotSurfaceStyle | None = None
    """Surface style."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.marker_style is None and self.surface_style is None:
            # Default to circle marker if neither is specified
            self.marker_style = PlotMarkerStyle.CIRCLE
