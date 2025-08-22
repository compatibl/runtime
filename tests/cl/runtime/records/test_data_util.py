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

from cl.runtime.parsers.locale import Locale
from cl.runtime.parsers.locale_key import LocaleKey
from cl.runtime.records.data_util import DataUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.settings.labels.class_label import ClassLabel
from cl.runtime.settings.labels.class_label_key import ClassLabelKey
from stubs.cl.runtime import StubDataclass, StubDataclassKey
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassSingleton


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
        DataUtil.full_build(sample, TypeHint.for_class(type(sample)))


def test_required():
    """Test validation of the field type during build."""

    samples = [
        ClassLabelKey(),  # noqa - missing a required field in key
        ClassLabel(class_name="en-US"),  # noqa - missing a required field in record
    ]

    for sample in samples:
        with pytest.raises(Exception):
            DataUtil.full_build(sample, TypeHint.for_class(type(sample)))


def test_field_type():
    """Test validation of the field type during build."""

    samples = [
        StubDataclass(id=123),  # noqa - wrong primitive type in key
        StubDataclassDerived(id=123),   # noqa - wrong primitive type in record
        StubDataclass(id=StubDataclassKey()),   # noqa - complex instead of primitive type
        StubDataclass(id=StubDataclassKey()),  # noqa - unrelated type
    ]

    for sample in samples:
        with pytest.raises(Exception):
            DataUtil.full_build(sample, TypeHint.for_class(type(sample)))


if __name__ == "__main__":
    pytest.main([__file__])
