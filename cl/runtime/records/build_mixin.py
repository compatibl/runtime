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

from typing_extensions import Self

from cl.runtime.records.build_what_enum import BuildWhatEnum
from cl.runtime.records.record_util import RecordUtil


class BuildMixin:
    """Optional mixin class adding build(), code must not rely on inheritance from this class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    def build(self, *, what: BuildWhatEnum = BuildWhatEnum.NEW) -> Self:
        """
        First invoke this 'build' method recursively for all of the object's non-primitive fields
        (including protected and private fields) in the order of declaration, and after this:
        (1) invoke 'init' method of this class and its ancestors in the order from base to derived
        (2) invoke freeze
        (3) validate against the type declaration
        Return self to enable method chaining.
        """
        return RecordUtil.build(self, what=what)
