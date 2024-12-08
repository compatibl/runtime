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
from typing import List


class MethodUtil:
    """Utilities for working with functions and methods."""

    @classmethod
    def is_implemented(cls, type_or_obj: Any, method_name: str) -> bool:
        """Return True if the method is implemented (present and not abstract)."""
        method = getattr(type_or_obj, method_name, None)
        return method is not None and not getattr(method, "__isabstractmethod__", False)
