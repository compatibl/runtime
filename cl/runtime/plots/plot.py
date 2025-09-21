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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.plots.plot_key import PlotKey
from cl.runtime.plots.plotting_engine import PlottingEngine
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Plot(PlotKey, RecordMixin, ABC):
    """Base class for plot objects."""

    title: str = required()
    """Plot title."""

    plotting_engine: PlottingEngine = PlottingEngine.MATPLOTLIB
    """Plotting engine (defaults to Matplotlib for vector graphics output)."""

    def get_key(self) -> PlotKey:
        return PlotKey(plot_id=self.plot_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.plot_id is None:
            # Use globally unique UUIDv7-based timestamp if not specified
            self.plot_id = Timestamp.create()
        if self.title is None:
            # Use plot_id as title if not specified
            self.title = self.plot_id

    def view_plot(self):
        """Default plot viewer."""
        return self.get_view()

    @abstractmethod
    def get_view(self) -> None:
        """Return a view object for the plot."""  # TODO: Refactor and fix return type hint

    @abstractmethod
    def save(self, format_: str = "png") -> None:
        """Save in given format to 'base_dir/plot_id.format_'."""
