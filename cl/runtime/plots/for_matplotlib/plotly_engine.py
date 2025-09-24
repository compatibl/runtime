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
from cl.runtime.plots.plot_color import PlotColor
from cl.runtime.plots.plot_line_style import PlotLineStyle
from cl.runtime.plots.plot_surface_style import PlotSurfaceStyle
from cl.runtime.plots.plotting_engine import PlottingEngine
from cl.runtime.plots.scatter_plot_2d import ScatterPlot2D
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
                color_css = self._to_css_color(values.color)
                colorscale = [[0.0, color_css], [1.0, color_css]]
                marker_dict = {}
                if values.marker_style is not None:
                    # TODO: !!!! Map marker_style to Plotly marker attributes
                    pass

                # If a solid surface is requested, render as a continuous surface
                if values.surface_style == PlotSurfaceStyle.SOLID:

                    # Fallback to markers if data cannot form a grid
                    fig.add_trace(
                        go.Mesh3d(
                            x=values.x,
                            y=values.y,
                            z=values.z,
                            colorscale=colorscale,
                            showscale=False,
                            opacity=0.8,
                            showlegend=True,
                            name=values.legend,
                            intensity=values.z
                        )
                    )
                else:
                    # Default: render as markers
                    fig.add_trace(
                        go.Scatter3d(
                            x=values.x,
                            y=values.y,
                            z=values.z,
                            mode="markers",
                            marker={"color": color_css, "size": 2, **marker_dict},
                            name=values.legend,
                        )
                    )
            fig.update_layout(
                scene=dict(
                    xaxis_title=plot.x_label or "",
                    yaxis_title=plot.y_label or "",
                    zaxis_title=plot.z_label or "",
                    xaxis=dict(range=plot.x_lim) if plot.x_lim else {},
                    yaxis=dict(range=plot.y_lim) if plot.y_lim else {},
                    zaxis=dict(range=plot.z_lim) if plot.z_lim else {},
                    # Axis background and grid visibility
                    xaxis_backgroundcolor="white",
                    xaxis_showgrid=False,
                    yaxis_backgroundcolor="white",
                    yaxis_showgrid=False,
                    zaxis_backgroundcolor="white",
                    zaxis_showgrid=False,
                    # Aspect ratio mode ('data' ensures that aspect ratio matches x-y-z data ranges)
                    aspectmode='data',
                ),
                showlegend=True,
                legend=dict(
                    # Legend styling
                    font=dict(size=15),
                    bordercolor="black",
                    borderwidth=2,
                    bgcolor="white",
                    # Legend positioning
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=0.01,
                    # Keep legend item sizes consistent
                    itemsizing='constant',
                )
            )
            html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
            return html.encode("utf-8")

        elif isinstance(plot, ScatterPlot2D):
            # Render ScatterPlot2D to HTML
            fig = go.Figure()
            for values in plot.data:
                color_css = self._to_css_color(values.color)
                marker_dict = {}
                if values.marker_style is not None:
                    # TODO: !!!! Map marker_style to Plotly marker attributes
                    pass

                if values.line_style == PlotLineStyle.SOLID:
                    # For 2D, interpret a solid surface as a continuous line
                    fig.add_trace(
                        go.Scatter(
                            x=values.x,
                            y=values.y,
                            mode="lines",
                            line={"color": color_css},
                            name=values.legend,
                        )
                    )
                else:
                    # Default: render as markers
                    fig.add_trace(
                        go.Scatter(
                            x=values.x,
                            y=values.y,
                            mode="markers",
                            marker={"color": color_css, "size": 6, **marker_dict},
                            name=values.legend,
                        )
                    )

            fig.update_layout(
                xaxis_title=plot.x_label or "",
                yaxis_title=plot.y_label or "",
                xaxis=dict(range=plot.x_lim) if plot.x_lim else {},
                yaxis=dict(range=plot.y_lim) if plot.y_lim else {},
                showlegend=True,
            )
            html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
            return html.encode("utf-8")
        else:
            raise RuntimeError(f"{typenameof(self)} does not support rendering of {typenameof(plot)} to HTML.")

    def _to_css_color(self, color: PlotColor) -> str:
        """Convert color to a CSS string."""
        if color is None:
            # Default to blue
            return "blue"
        else:
            mapping = {
                PlotColor.BLACK: "black",
                PlotColor.WHITE: "white",
                PlotColor.RED: "red",
                PlotColor.GREEN: "green",
                PlotColor.BLUE: "blue",
                PlotColor.CYAN: "cyan",
                PlotColor.MAGENTA: "magenta",
                PlotColor.YELLOW: "yellow",
                PlotColor.ORANGE: "orange",
                PlotColor.PURPLE: "purple",
                PlotColor.BROWN: "brown",
                PlotColor.PINK: "pink",
                PlotColor.GRAY: "gray",
                PlotColor.OLIVE: "olive",
                PlotColor.TEAL: "teal",
                PlotColor.NAVY: "navy",
            }
            if result := mapping.get(color):
                return result
            else:
                raise RuntimeError(f"Color enum {color} is not supported by {typenameof(self)}")
