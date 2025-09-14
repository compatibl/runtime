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

from uuid import UUID
import datetime as dt
import numpy as np
import pytest
from bson import Int64

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_abstract_type, is_ndarray_type, FloatVector, FloatMatrix, FloatCube, \
    is_data_type, is_primitive_type, is_type
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_key_or_record_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_util import RecordUtil
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey


def test_functions():
    """Test functions defined in the protocols module."""

    # Class groups
    primitive_types_and_aliases = (
        str,
        float,
        np.float64,
        np.dtype[np.float64],
        bool,
        int,
        Int64,
        dt.date,
        dt.time,
        dt.datetime,
        UUID,
        bytes,
        type,
    )
    abstract_types = (
        KeyMixin,
        RecordMixin,
        DataMixin,
    )
    data_types = (
        DataMixin,
        DataclassMixin,
        StubDataclassData,
    )
    key_types = (
        KeyMixin,
        StubDataclassKey,
    )
    record_types = (
        RecordMixin,
        StubDataclass,
        StubDataclassDerived,
    )

    # For ndarray, the list also includes generic aliases
    ndarray_types_and_aliases = (
        np.ndarray,
        FloatVector,
        FloatMatrix,
        FloatCube,
    )

    # Combined lists
    key_or_record_types = key_types + record_types
    data_key_or_record_types = data_types + key_or_record_types

    # Everything
    all_types = primitive_types_and_aliases + abstract_types + data_types + key_types + record_types + ndarray_types_and_aliases

    # Test is_primitive_type
    for class_ in all_types:
        assert is_primitive_type(class_) == (class_ in primitive_types_and_aliases), f"{class_} is not abstract"

    # Test is_abstract_type
    for class_ in all_types:
        assert is_abstract_type(class_) == (class_ in abstract_types), f"{class_} is not abstract"

    # Test is_type
    for class_ in all_types:
        assert is_type(class_) == True
        
    # Test is_data_type
    for class_ in all_types:
        assert is_data_type(class_) == (
            class_ in data_types
        )
        
    # Test is_key_type
    for class_ in all_types:
        assert is_key_type(class_) == (
            class_ in key_types
        )
        
    # Test is_record_type
    for class_ in all_types:
        assert is_record_type(class_) == (
            class_ in record_types
        )

    # Test is_key_or_record_type
    for class_ in all_types:
        assert is_key_or_record_type(class_) == (
            class_ in key_or_record_types
        )
        
    # Test is_data_type
    for class_ in all_types:
        assert is_data_key_or_record_type(class_) == (
            class_ in data_key_or_record_types
        )

    # Test is_ndarray_type
    for class_ in all_types:
        assert is_ndarray_type(class_) == (class_ in ndarray_types_and_aliases)
    for class_ in ndarray_types_and_aliases:
        assert is_ndarray_type(class_)


if __name__ == "__main__":
    pytest.main([__file__])
