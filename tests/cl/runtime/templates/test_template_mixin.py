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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.templates.fstring_template_engine import FstringTemplateEngine
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime.templates.stub_template import StubTemplate


def test_template_mixin(pytest_default_db):
    """Test rendering TemplateMixin."""

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
    template = StubTemplate(body=body, engine=engine).build()
    result = template.render(data)
    assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
