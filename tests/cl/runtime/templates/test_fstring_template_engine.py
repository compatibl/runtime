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
from cl.runtime.templates.fstring_template_engine import FstringTemplateEngine
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields


def test_primitive_fields():
    """Test rendering StubDataclassPrimitiveFields."""

    engine = FstringTemplateEngine()
    data = StubDataclassPrimitiveFields()
    body = (
        "obj_str_field: {obj_str_field}\n"
        "obj_str_with_eol_field: {obj_str_with_eol_field}\n"
        "obj_str_timestamp_field: {obj_str_timestamp_field}\n"
        "obj_float_field: {obj_float_field}\n"
        "obj_bool_field: {obj_bool_field}\n"
        "obj_int_field: {obj_int_field}\n"
        "obj_long_field: {obj_long_field}\n"
        "obj_date_field: {obj_date_field}\n"
        "obj_time_field: {obj_time_field}\n"
        "obj_date_time_field: {obj_date_time_field}\n"
        "obj_uuid_field: {obj_uuid_field}\n"
        "obj_bytes_field: {obj_bytes_field}\n"
        "obj_bytes_large_field: {obj_bytes_large_field}\n"
        "obj_int_enum_field: {obj_int_enum_field}\n"
    )

    # Since bytes and large bytes might not render nicely, we format them carefully
    expected_result = (
        "obj_str_field: abc\n"
        "obj_str_with_eol_field: abc\ndef\n"
        "obj_str_timestamp_field: 2023-05-01T10:15:30.000Z-1a1a1a1a1a1a1a1a1a1a\n"
        "obj_float_field: 1.23\n"
        "obj_bool_field: true\n"
        "obj_int_field: 123\n"
        "obj_long_field: 9007199254740991\n"
        "obj_date_field: 2003-05-01\n"
        "obj_time_field: 10:15:30.000\n"
        "obj_date_time_field: 2003-05-01T10:15:00.000Z\n"
        "obj_uuid_field: 1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a\n"
        "obj_bytes_field: ZG54\n"
        "obj_bytes_large_field: ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
        "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
        "ZG54ZG54\n"
        "obj_int_enum_field: EnumValue1\n"
    )

    # Render and validate
    result = engine.render(body, data)
    assert result == expected_result


def test_nested_fields():
    """Test rendering StubDataclassPrimitiveFields."""

    engine = FstringTemplateEngine()
    data = StubDataclassNestedFields()
    body = (
        "base_field.str_field: {base_field.str_field}\n"
        "base_field.int_field: {base_field.int_field}\n"
        "polymorphic_derived_field.double_derived_str_field: {polymorphic_derived_field.double_derived_str_field}\n"
    )

    # Since bytes and large bytes might not render nicely, we format them carefully
    expected_result = (
        "base_field.str_field: abc\n"
        "base_field.int_field: 123\n"
        "polymorphic_derived_field.double_derived_str_field: double_derived\n"
    )

    # Render and validate
    result = engine.render(body, data)
    assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
