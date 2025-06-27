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
    def cast(cls, result_type: type[TObj], obj: Any) -> TObj:
        """
        Cast obj to result_type after checking it is an instance of result_type, error message otherwise.
        This provides a runtime-checked alternative to typing.cast which does not check anything at runtime.
        Pass through None.
        """
        if obj is None or isinstance(obj, result_type):
            return obj
        else:
            raise RuntimeError(
                f"Cannot cast an object of type {TypeUtil.name(obj)} to type {TypeUtil.name(result_type)}."
            )
