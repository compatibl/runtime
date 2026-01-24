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
import numpy as np
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import FloatArray
from cl.runtime.records.protocols import FloatCube
from cl.runtime.records.protocols import FloatMatrix
from cl.runtime.records.protocols import FloatVector
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


@dataclass(slots=True, kw_only=True)
class StubDataclassNumpyFields(StubDataclass):
    """Stub record with numpy fields."""

    float_array: FloatArray = required(default_factory=lambda: np.array([1.0, 2.0]))
    """NumPy array with dtype=np.float64 and any number of dimensions."""

    float_vector: FloatVector = required(default_factory=lambda: np.array([1.0, 2.0]))
    """1D ndarray."""

    float_matrix: FloatMatrix = required(default_factory=lambda: np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
    """2D ndarray."""

    float_cube: FloatCube = required(
        default_factory=lambda: np.array(
            [
                [[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0], [9.0, 10.0, 11.0, 12.0]],
                [[13.0, 14.0, 15.0, 16.0], [17.0, 18.0, 19.0, 20.0], [21.0, 22.0, 23.0, 24.0]],
            ]
        )
    )
    """3D ndarray."""

    # untyped_ndarray: np.ndarray | None = None  # noqa Not a valid type hint, this is an invalid sample
    # """Stub field."""
