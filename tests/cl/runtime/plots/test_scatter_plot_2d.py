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

import numpy as np
from cl.runtime.plots.for_matplotlib.plotly_engine import PlotlyEngine
from cl.runtime.plots.plot_line_style import PlotLineStyle
from cl.runtime.plots.scatter_plot_2d import ScatterPlot2D
from cl.runtime.plots.scatter_values_2d import ScatterValues2D


def create_plot():
    """Create plot for testing."""
    # Create a grid for the surface
    x_grid = np.linspace(0, 4, 20)
    y_grid = 0.5 * x_grid + 0.3 * x_grid**2

    data = [
        ScatterValues2D(
            x=[1, 2, 3],
            y=[4, 5, 6],
            legend="Scatter",
        ).build(),
        ScatterValues2D(
            x=list(x_grid.flatten()),
            y=list(y_grid.flatten()),
            legend="Surface",
            marker_style=None,
            line_style=PlotLineStyle.SOLID,
        ).build(),
    ]
    plot = ScatterPlot2D(
        data=data,
        x_label="X Axis",
        y_label="Y Axis",
        x_lim=(0, 5),
        y_lim=(0, 10),
    ).build()
    return plot


def test_html(work_dir_fixture):
    """Test rendering to HTML."""

    # Render
    plot = create_plot()
    engine = PlotlyEngine()
    html_bytes = engine.render_html(plot)

    # Basic checks of result
    assert isinstance(html_bytes, bytes)
    html = html_bytes.decode("utf-8")
    assert "plotly" in html.lower()
    assert "X Axis" in html

    # Save to disk
    with open("scatter_plot_2d.plotly.html", "w", encoding="utf-8") as f:
        f.write(html)
