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

from typing import Any, TypeGuard
from cl.runtime.records.builder_mixin import BuilderMixin
from cl.runtime.records.protocols import is_builder
from cl.runtime.records.typename import typename


class BuilderChecks:
    """Runtime checks for the builder pattern."""

    @classmethod
    def guard_frozen(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderMixin]:
        """Check if the argument is frozen."""
        if is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not frozen.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} does not have build() method.")
        else:
            return False

    @classmethod
    def guard_frozen_or_none(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderMixin | None]:
        """Check if the argument is frozen or None."""
        if obj is None:
            return True
        elif is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not frozen or None.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} does not have build() method and is not None.")
        else:
            return False
