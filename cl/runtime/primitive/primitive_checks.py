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

from cl.runtime.records.protocols import TObj
from cl.runtime.records.typename import typename


class PrimitiveChecks:
    """Runtime checks for primitive fields."""

    @classmethod
    def guard_none(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[None]:
        """Confirm that the argument is None."""
        if obj is None:
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} is not None.")
        else:
            return False

    @classmethod
    def guard_not_none(cls, obj: TObj | None, *, raise_on_fail: bool = True) -> TypeGuard[TObj]:
        """Confirm that the argument is not None."""
        if obj is not None:
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} is None.")
        else:
            return False

