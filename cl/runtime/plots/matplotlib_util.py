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

from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.image import AxesImage


class MatplotlibUtil:
    """Utilities for plots created using Matplotlib."""

    @classmethod
    def heatmap(
        cls,
        data: np.ndarray,
        row_labels: List[str],
        col_labels: List[str],
        ax=None,
        **kwargs,
    ):
        """
        Create a heatmap from a numpy array and two lists of labels.

        Args:
            data: A 2D numpy array of shape (M, N).
            row_labels: A list or array of length M with the labels for the rows.
            col_labels: A list or array of length N with the labels for the columns.
            ax: A `matplotlib.axes.Axes` instance to which the heatmap is plotted (optional)
            kwargs: All other arguments are forwarded to `ax.imshow` (optional)
        """

        if ax is None:
            ax = plt.gca()

        # Plot the heatmap
        im = ax.imshow(data, **kwargs)

        # Show all ticks and label them with the respective list entries.
        ax.set_xticks(np.arange(data.shape[1]), labels=col_labels)
        ax.set_yticks(np.arange(data.shape[0]), labels=row_labels)

        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

        # Rotate the tick labels and set their alignment.
        plt.setp(ax.get_xticklabels(), rotation=-30, ha="right", rotation_mode="anchor")

        # Turn spines off and create white grid.
        ax.spines[:].set_visible(False)

        ax.set_xticks(np.arange(data.shape[1] + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(data.shape[0] + 1) - 0.5, minor=True)
        ax.grid(which="minor", color="w", linestyle="-", linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)

        return im

    @classmethod
    def annotate_heatmap(
        cls,
        im: AxesImage,
        labels: List[List[str]],
        text_colors: Union[str, Tuple[str]] = ("black", "white"),
        threshold: float | None = None,
        **kwargs,  # TODO: Avoid **kwargs
    ):
        """
        Annotate a heatmap.

        Args:
            im: The AxesImage to be labeled.
            labels: Label for each cell
            text_colors: One or two colors, if two are provided the first is used for values below a threshold and
                    the second for those above, optional
            threshold: Value in data units according to which the colors from text_colors are applied (optional)
            kwargs: All other arguments are forwarded to `im.axes.text` to create the text labels (optional)
        """

        data = im.get_array()

        # Normalize the threshold to the images color range.
        if threshold is not None:
            threshold = im.norm(threshold)

        # Set default alignment to center, but allow it to be
        # overwritten by kwargs.
        kw = dict(horizontalalignment="center", verticalalignment="center")
        kw.update(kwargs)

        # Loop over the data and create a `Text` for each "pixel".
        # Change the text's color depending on the data.
        texts = []
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                kw.update(
                    color=(
                        text_colors[int(im.norm(data[i, j]) < threshold)]
                        if isinstance(text_colors, tuple)
                        else text_colors
                    ),
                )
                text = im.axes.text(j, i, labels[i][j], **kw)
                texts.append(text)

        return texts

    @classmethod
    def no_metadata(cls) -> Dict[str, str]:
        """Return empty metadata for Matplotlib to prevent version changes from creating test diffs."""
        return {
            "Title": "",
            "Author": "",
            "Description": "",
            "Copyright": "",
            "CreationTime": "",
            "Software": "",
            "Disclaimer": "",
            "Warning": "",
            "Source": "",
            "Comment": "",
        }
