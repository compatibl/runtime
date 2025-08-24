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

from cl.runtime.plots.line_plot import LinePlot
from cl.runtime.plots.plot import Plot


class StubLinePlots:
    """Create LinePlot stubs."""

    @classmethod
    def get_one_line_plot(cls, plot_id: str) -> Plot:
        """Get basic plot."""
        result = LinePlot(plot_id=plot_id, title="LinePlot")
        result.x_values = [1.0, 2.0, 3.0]
        result.lines = {
            "line_1": [4.0, 3.0, 7.0],
        }
        return result.build()

    @classmethod
    def get_two_line_plot(cls, plot_id: str) -> Plot:
        """Get basic plot."""
        result = LinePlot(plot_id=plot_id, title="LinePlot")
        result.x_values = [1.0, 2.0, 3.0]
        result.lines = {"line_1": [4.0, 3.0, 7.0], "line_2": [5.0, 6.0, 1.0]}
        return result.build()
