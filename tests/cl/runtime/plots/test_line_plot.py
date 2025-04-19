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

import pytest
from cl.runtime.plots.group_bar_plot import GroupBarPlot
from cl.runtime.plots.line_plot import LinePlot
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa


def test_one_line(pytest_work_dir):
    plot = LinePlot(plot_id="line_plot.test_one_line")
    plot.x_values = [1, 2, 3]
    plot.lines = {
        "line_1": [4,3,7]
    }
    plot.save_png()

def test_two_lines(pytest_work_dir):
    plot = LinePlot(plot_id="line_plot.test_two_lines")
    plot.x_values = [1, 2, 3]
    plot.lines = {
        "line_1": [4, 3, 7],
        "line_2": [5, 6, 1]
    }
    plot.save_png()


if __name__ == "__main__":
    pytest.main([__file__])
