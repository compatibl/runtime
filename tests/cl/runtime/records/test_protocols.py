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
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_abstract
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.record_util import RecordUtil
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassKey


def test_functions():
    """Test functions defined in the protocols module."""

    # Classes
    key_mixin_class = KeyMixin
    non_data_class = RecordUtil
    data_class = StubDataclassData
    key_class = StubDataclassKey
    record_class = StubDataclass
    derived_class = StubDataclassDerived

    # Class groups
    all_classes = (
        key_mixin_class,
        non_data_class,
        data_class,
        key_class,
        record_class,
        derived_class,
    )
    abstract_classes = (key_mixin_class,)
    data_classes = (
        data_class,
        key_class,
        record_class,
        derived_class,
    )
    key_or_record_classes = (
        key_class,
        record_class,
        derived_class,
    )
    key_classes = (key_class,)
    record_classes = (
        record_class,
        derived_class,
    )

    # Test is_abstract
    for class_ in all_classes:
        assert is_abstract(class_) == (class_ in abstract_classes), f"{class_} is not abstract"

    # Test is_data
    for class_ in all_classes:
        assert is_data(class_) == (class_ in data_classes), f"{class_} is not a data class"
        if class_ not in abstract_classes:
            assert is_data(class_()) == (class_ in data_classes), f"{class_} is not a data class instance"

    # Test is_key_or_record
    for class_ in all_classes:
        assert is_key_or_record(class_) == (class_ in key_or_record_classes), f"{class_} is not a key or record class"
        if class_ not in abstract_classes:
            assert is_key_or_record(class_()) == (
                class_ in key_or_record_classes
            ), f"{class_} is not a key or record instance"

    # Test is_key
    for class_ in all_classes:
        assert is_key(class_) == (class_ in key_classes), f"{class_} is not a key class"
        if class_ not in abstract_classes:
            assert is_key(class_()) == (class_ in key_classes), f"{class_} is not a key instance"

    # Test is_record
    for class_ in all_classes:
        assert is_record(class_) == (class_ in record_classes), f"{class_} is not a record class"
        if class_ not in abstract_classes:
            assert is_record(class_()) == (class_ in record_classes), f"{class_} is not a record instance"


if __name__ == "__main__":
    pytest.main([__file__])
