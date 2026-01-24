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
from cl.runtime.records.data_util import DataUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.settings.labels.type_label import TypeLabel
from cl.runtime.settings.labels.type_label_key import TypeLabelKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived import StubDataclassDoubleDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_other_derived import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_singleton import StubDataclassSingleton


def test_data_build():
    """Test DataUtil.full_build method."""

    samples = [
        StubDataclassOptionalFields(id="abc7"),
        StubDataclass(id="abc1"),
        StubDataclassNestedFields(id="abc2"),
        StubDataclassComposite(),
        StubDataclassDerived(id="abc3"),
        StubDataclassDoubleDerived(id="abc4"),
        StubDataclassOtherDerived(id="abc5"),
        StubDataclassListFields(id="abc6"),
        StubDataclassOptionalFields(id="abc7"),
        StubDataclassDictFields(id="abc8"),
        StubDataclassDictListFields(id="abc9"),
        StubDataclassListDictFields(id="abc10"),
        StubDataclassPrimitiveFields(key_str_field="abc11"),
        StubDataclassSingleton(),
    ]

    for sample in samples:
        DataUtil.build_(sample, TypeHint.for_type(type(sample)))


def test_required():
    """Test validation of the field type during build."""

    samples = [
        TypeLabelKey(),  # noqa - missing a required field in key
        TypeLabel(type_name="en-US"),  # noqa - missing a required field in record
    ]

    for sample in samples:
        with pytest.raises(Exception):
            DataUtil.build_(sample, TypeHint.for_type(type(sample)))


def test_field_type():
    """Test validation of the field type during build."""

    samples = [
        StubDataclass(id=123),  # noqa - wrong primitive type in key
        StubDataclassDerived(id=123),  # noqa - wrong primitive type in record
        StubDataclass(id=StubDataclassKey()),  # noqa - complex instead of primitive type
        StubDataclass(id=StubDataclassKey()),  # noqa - unrelated type
    ]

    for sample in samples:
        with pytest.raises(Exception):
            DataUtil.build_(sample, TypeHint.for_type(type(sample)))


if __name__ == "__main__":
    pytest.main([__file__])
