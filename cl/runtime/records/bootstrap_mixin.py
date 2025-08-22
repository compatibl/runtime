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
from typing import Self
from memoization import cached
from cl.runtime.records.bootstrap_util import BootstrapUtil
from cl.runtime.records.builder_mixin import BuilderMixin
from cl.runtime.serializers.slots_util import SlotsUtil


class BootstrapMixin(BuilderMixin, ABC):
    """Dataclasses base for lightweight classes that do not require validation against the schema."""

    __slots__ = ()

    @classmethod
    @cached
    def get_field_names(cls) -> tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""
        return SlotsUtil.get_field_names(cls)

    def build(self) -> Self:
        """
        The implementation of the build method in BootstrapMixin performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Calls its 'mark_frozen' method without performing validation against the schema
        """
        return BootstrapUtil.bootstrap_build(self)
