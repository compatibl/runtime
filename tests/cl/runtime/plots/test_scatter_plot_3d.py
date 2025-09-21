import numpy as np

from cl.runtime.plots.for_matplotlib.plotly_engine import PlotlyEngine
from cl.runtime.plots.scatter_plot_3d import ScatterPlot3D
from cl.runtime.plots.scatter_values_3d import ScatterValues3D
from cl.runtime.plots.plot_surface_style import PlotSurfaceStyle


def create_plot():
    """Create plot for testing."""
    # Create a grid for the surface
    x = np.linspace(0, 4, 20)
    y = np.linspace(0, 8, 20)
    x_grid, y_grid = np.meshgrid(x, y)
    z_grid = 0.5 * x_grid + 0.3 * y_grid**2  # Simple surface function

    data = [
        ScatterValues3D(
            x=[1, 2, 3],
            y=[4, 5, 6],
            z=[7, 8, 9],
        ).build(),
        ScatterValues3D(
            x=list(x_grid.flatten()),
            y=list(y_grid.flatten()),
            z=list(z_grid.flatten()),
            marker_style=None,
            surface_style=PlotSurfaceStyle.SOLID,
        ).build(),
    ]
    plot = ScatterPlot3D(
        data=data,
        x_label="X Axis",
        y_label="Y Axis",
        z_label="Z Axis",
        x_lim=(0, 5),
        y_lim=(0, 10),
        z_lim=(0, 15)
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
    html = html_bytes.decode('utf-8')
    assert "plotly" in html.lower()
    assert "X Axis" in html

    # Save to disk
    with open("scatter_plot_3d.plotly.html", "w", encoding="utf-8") as f:
        f.write(html)
