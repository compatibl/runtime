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

import io
import os
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
import matplotlib
from matplotlib import pyplot as plt
from cl.runtime import View
from cl.runtime.backend.core.ui_app_state import UiAppState
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.plots.matplotlib_util import MatplotlibUtil
from cl.runtime.plots.plot import Plot
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.views.png_view import PngView

# Use non-UI matplotlib backend to prevent Tkl/Tk errors
matplotlib.use("Agg")


@dataclass(slots=True, kw_only=True)
class MatplotlibPlot(Plot, ABC):
    """Base class for plot objects created using Matplotlib package."""

    @abstractmethod
    def _create_figure(self) -> plt.Figure:
        """Return Matplotlib figure object for the plot."""

    def get_view(self) -> PngView:
        """Return a view object for the plot, implement using 'create_figure' method."""

        # Create figure
        fig = self._create_figure()

        # Check if transparency required
        is_dark_theme = UiAppState.get_current_user_app_theme() == "Dark"  # TODO: Move to PlotSettings
        transparent = is_dark_theme

        # Save to bytes
        png_buffer = io.BytesIO()
        fig.savefig(png_buffer, format="png", transparent=transparent, metadata=MatplotlibUtil.no_png_metadata())

        # Get the PNG image bytes and wrap in PngView
        png_bytes = png_buffer.getvalue()
        result = PngView(png_bytes=png_bytes)
        return result

    def save(self, format_: str = "png") -> None:
        """Save in given format to 'base_dir/plot_id.format_', implement using 'create_figure' method."""
        if format_ not in ("png", "svg"):
            raise RuntimeError(f"Unsupported figure save format: {format_}.")
        # Create figure
        fig = self._create_figure()

        # Create directory if does not exist
        base_dir = QaUtil.get_test_dir()
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # Check that plot_id is set
        if self.plot_id is None or self.plot_id == "":
            raise RuntimeError("Cannot save figure because 'plot_id' field is not set.")

        # Transparent in dark theme
        transparent = self.is_dark_theme()

        # Save
        file_path = os.path.join(base_dir, f"{self.plot_id}.{format_}")
        metadata = MatplotlibUtil.no_svg_metadata() if format_ == "svg" else MatplotlibUtil.no_png_metadata()
        fig.savefig(
            file_path,
            transparent=transparent,
            metadata=metadata,
            dpi=100,
            format=format_,
            bbox_inches="tight",
            pad_inches=0.1,
        )

    @classmethod
    def is_dark_theme(cls) -> bool:
        """True if dark UI theme when invoked from a process, and False inside tests."""
        if ProcessContext.is_testing():
            result = False
        else:
            result = UiAppState.get_current_user_app_theme() == "Dark"  # TODO: Move to PlotSettings
        return result

    @classmethod
    def _get_pyplot_theme(cls) -> str:
        """Get value to be set as matplotlib.pyplot theme."""
        theme = "dark_background" if cls.is_dark_theme() else "default"
        return theme
