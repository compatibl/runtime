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
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassSingleton


def test_build():
    """Test BuildUtil.validate method."""

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
        sample.build()


if __name__ == "__main__":
    pytest.main([__file__])
