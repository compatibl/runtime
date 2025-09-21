import pytest

from cl.runtime.plots.for_matplotlib.plotly_engine import PlotlyEngine
from cl.runtime.plots.scatter_plot_3d import ScatterPlot3D
from cl.runtime.plots.scatter_values_3d import ScatterValues3D

def create_plot():
    """Create plot for testing."""
    data = [
        ScatterValues3D(x=[1, 2, 3], y=[4, 5, 6], z=[7, 8, 9])
    ]
    plot = ScatterPlot3D(
        data=data,
        x_label="X Axis",
        y_label="Y Axis",
        z_label="Z Axis",
        x_lim=(0, 5),
        y_lim=(0, 10),
        z_lim=(0, 15)
    )
    return plot

def test_html(work_dir_fixture):
    """Test rendering to HTML."""

    # Render
    plot = create_plot()
    engine = PlotlyEngine()
    html_bytes = engine.render_html(plot)

    # Basic checks of result
    assert isinstance(html_bytes, bytes)
    html = html_bytes.decode('utf-8')
    assert "plotly" in html.lower()
    assert "X Axis" in html

    # Save to disk
    with open("scatter_plot_3d.plotly.html", "w", encoding="utf-8") as f:
        f.write(html)
