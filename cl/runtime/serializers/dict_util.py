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

from typing import Dict, Mapping, Callable, Any
from frozendict import frozendict  # noqa


class DictUtil:
    """Helper methods for dictionaries."""

    @classmethod
    def with_filter_values(cls, data: Mapping[str, Any], predicate: Callable[[Any], bool]) -> Dict[str, Any]:
        """Recursively filter values based on the predicate."""
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = cls.filter_values(value, predicate)
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                container_type = type(value)
                filtered_list = container_type(item for item in value if predicate(item))
                if filtered_list:
                    result[key] = filtered_list
            elif predicate(value):
                result[key] = value
        return result
