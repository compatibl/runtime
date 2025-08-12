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

from typing import Any
from cl.runtime.records.protocols import TObj
from cl.runtime.records.type_util import TypeUtil


class CastUtil:
    """Helper class for safe downcasting."""

    @classmethod
    def cast(cls, cast_to: type[TObj], obj: Any) -> TObj:
        """
        Cast obj to type cast_to after checking it is an instance of cast_to, error message otherwise.
        This provides a runtime-checked alternative to typing.cast which does not check anything at runtime.
        """
        if obj is not None:
            return cls.cast_or_none(cast_to, obj)
        else:
            raise RuntimeError(f"Cannot cast None to type {TypeUtil.name(cast_to)}, use cast_or_none to allow.")

    @classmethod
    def cast_or_none(cls, cast_to: type[TObj], obj: Any) -> TObj:
        """
        Cast obj to type cast_to after checking it is an instance of cast_to or None, error message otherwise.
        This provides a runtime-checked alternative to typing.cast which does not check anything at runtime.
        """
        if obj is None or isinstance(obj, cast_to):
            return obj
        else:
            raise RuntimeError(f"Cannot cast an object of type {TypeUtil.name(obj)} to type {TypeUtil.name(cast_to)}.")
