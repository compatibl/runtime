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

from abc import ABC
from cl.runtime.decorators.attrs_record_decorator import attrs_record
from typing import List, Optional

from cl.runtime import Record
from cl.runtime.schema.decl.module_key import ModuleKey
from cl.runtime.schema.decl.package_key import PackageKey
from cl.runtime.decorators.data_field_decorator import data_field


@attrs_record
class Module(ModuleKey, Record):
    """
    Represents a group of related types under a common namespace or directory.
    """

    label: Optional[str] = data_field()
    """Module label."""

    comment: Optional[str] = data_field()
    """Module additional information."""

    dependences: Optional[List[ModuleKey]] = data_field()
    """Module dependences."""

    package: PackageKey = data_field()
    """Package refence."""

    copyright_: Optional[str] = data_field(name='Copyright')
    """Company name used in Copyright src header."""