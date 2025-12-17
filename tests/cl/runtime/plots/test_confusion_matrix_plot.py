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
from pathlib import Path
import pandas as pd
from matplotlib import pyplot as plt
from cl.runtime.plots.confusion_matrix_plot import ConfusionMatrixPlot
from cl.runtime.qa.regression_guard import RegressionGuard


def test_smoke(work_dir_fixture):
    raw_data = pd.read_csv(Path(__file__).resolve().parent / "./test_confusion_matrix_plot.csv")


@pytest.mark.skip("Restore test when it becomes possible to override the default theme.")
def test_dark_theme(work_dir_fixture):
    """Test ConfusionMatrixPlot in dark mode using RegressionGuard."""

    raw_data = pd.read_csv(Path(__file__).resolve().parent / "./test_confusion_matrix_plot.csv")
    guard = RegressionGuard(ext="png", channel="matrix_plot")
    plot = ConfusionMatrixPlot(
        title="ConfusionMatrixPlot",
        expected_categories=raw_data["True Category"].values.tolist(),
        received_categories=raw_data["Predicted"].values.tolist(),
    ).build()
    fig = plot._create_figure()
    guard.write(fig)
    guard.verify()
    plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__])
