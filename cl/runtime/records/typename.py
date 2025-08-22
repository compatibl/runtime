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


def typename(instance_or_type: Any) -> str:
    """Return type name without module in PascalCase, or an alias if provided."""
    # TODO: Add support for aliases
    # Accept instance or type
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__
    return result


def qualname(instance_or_type: Any) -> str:
    """Return fully qualified type name with module in module.PascalCase format without applying any aliases."""
    # Accept instance or type
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = f"{type_.__module__}.{type_.__name__}"
    return result
