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
import plotly.graph_objects as go
import plotly.io as pio
from cl.runtime.plots.plot import Plot
from cl.runtime.plots.plotting_engine import PlottingEngine
from cl.runtime.plots.scatter_plot_3d import ScatterPlot3D
from cl.runtime.records.typename import typenameof


@dataclass(slots=True, kw_only=True)
class PlotlyEngine(PlottingEngine):
    """Plotting engine using Plotly library."""

    def render_html(self, plot: Plot) -> bytes:
        """Render the plot to HTML."""

        if isinstance(plot, ScatterPlot3D):
            # Render ScatterPlot3D to HTML
            fig = go.Figure()
            for values in plot.data:
                marker_dict = {}
                if values.marker_style is not None:
                    # Optionally, map marker_style to Plotly marker attributes here
                    pass
                color = getattr(values.color, 'value', str(values.color)) if hasattr(values.color, 'value') else str(values.color)
                fig.add_trace(
                    go.Scatter3d(
                        x=values.x,
                        y=values.y,
                        z=values.z,
                        mode='markers',
                        marker={"color": color, "size": 2, **marker_dict}  # Setting marker size to 20% of default (default is ~10)
                    )
                )
            fig.update_layout(
                scene=dict(
                    xaxis_title=plot.x_label or '',
                    yaxis_title=plot.y_label or '',
                    zaxis_title=plot.z_label or '',
                    xaxis=dict(range=plot.x_lim) if plot.x_lim else {},
                    yaxis=dict(range=plot.y_lim) if plot.y_lim else {},
                    zaxis=dict(range=plot.z_lim) if plot.z_lim else {},
                )
            )
            html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
            return html.encode('utf-8')

        else:
            raise RuntimeError(f"{typenameof(self)} does not support rendering of {typenameof(plot)} to HTML.")
