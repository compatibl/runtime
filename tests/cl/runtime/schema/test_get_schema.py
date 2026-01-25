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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.schema.for_dataclasses.dataclass_type_decl import DataclassTypeDecl
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields


def test_method():
    """Test coroutine for /schema/typeV2 route."""

    sample_types = [
        StubDataclass,
        StubDataclassPrimitiveFields,
        StubDataclassListFields,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassOptionalFields,
    ]

    for sample_type in sample_types:
        result_obj = DataclassTypeDecl.for_type(sample_type)
        result_dict = BootstrapSerializers.FOR_UI.serialize(result_obj)

        guard = RegressionGuard(prefix=sample_type.__module__.rsplit(".", 1)[1]).build()
        guard.write(result_dict)

    RegressionGuard().build().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
