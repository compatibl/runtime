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

import numpy as np
import pytest
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_abstract_type, is_ndarray_type, FloatVector, FloatMatrix, FloatCube
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
    all_classes = (
        RecordUtil,
        DataMixin,
        KeyMixin,
        RecordMixin,
        DataclassMixin,
        StubDataclassData,
        StubDataclassKey,
        StubDataclass,
        StubDataclassDerived,
        np.ndarray,
    )
    abstract_classes = (
        KeyMixin,
        RecordMixin,
        DataMixin,
    )
    data_classes = (
        DataMixin,
        KeyMixin,
        RecordMixin,
        DataclassMixin,
        StubDataclassData,
        StubDataclassKey,
        StubDataclass,
        StubDataclassDerived,
    )
    key_or_record_classes = (
        KeyMixin,
        RecordMixin,
        StubDataclassKey,
        StubDataclass,
        StubDataclassDerived,
    )
    key_classes = (
        KeyMixin,
        StubDataclassKey,
    )
    record_classes = (
        RecordMixin,
        StubDataclass,
        StubDataclassDerived,
    )
    ndarray_classes_and_aliases = (
        np.ndarray,
        FloatVector,
        FloatMatrix,
        FloatCube,
    )

    # Test is_abstract_type
    for class_ in all_classes:
        assert is_abstract_type(class_) == (class_ in abstract_classes), f"{class_} is not abstract"

    # Test is_data_type
    for class_ in all_classes:
        assert is_data_key_or_record_type(class_) == (
            class_ in data_classes
        ), f"{class_} is not a data, key or record class"

    # Test is_key_or_record_type
    for class_ in all_classes:
        assert is_key_or_record_type(class_) == (
            class_ in key_or_record_classes
        ), f"{class_} is not a key or record class"

    # Test is_key_type
    for class_ in all_classes:
        assert is_key_type(class_) == (class_ in key_classes), f"{class_} is not a key class"

    # Test is_record_type
    for class_ in all_classes:
        assert is_record_type(class_) == (class_ in record_classes), f"{class_} is not a record class"

    # Test is_ndarray_type
    for class_ in all_classes:
        assert is_ndarray_type(class_) == (class_ in ndarray_classes_and_aliases), f"{class_} is not ndarray or its generic alias"
    for class_ in ndarray_classes_and_aliases:
        assert is_ndarray_type(class_)


if __name__ == "__main__":
    pytest.main([__file__])
