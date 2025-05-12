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
from typing_extensions import Self
from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.freezable_mixin import FreezableMixin
from cl.runtime.serializers.slots_util import SlotsUtil


class DataMixin(FreezableMixin, ABC):
    """Framework-neutral mixin adding 'build' and related methods to the class."""

    __slots__ = SlotsUtil.merge_slots(FreezableMixin)
    """To prevent creation of __dict__ in derived types."""

    def build(self) -> Self:
        """
        The implementation of the build method in DataMixin performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Validates root level object against the schema and calls its 'mark_frozen' method
        """
        return BuildUtil.typed_build(self)
