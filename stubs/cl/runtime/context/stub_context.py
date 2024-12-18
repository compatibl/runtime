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

from dataclasses import dataclass
from typing import Type

from cl.runtime.context.base_context import BaseContext


@dataclass(slots=True, kw_only=True)
class StubContext(BaseContext):
    """Base extension context."""

    @classmethod
    def get_key_type(cls) -> Type:
        """
        The lookup of current context for cls will be done using the type returned by this method as key.

        Notes:
            - Return as specific type rather than type(self) to avoid variation across derived types
            - The returned type may be a base context class or a dedicated key type
            - Contexts that have different key types are isolated from each other and have independent 'with' clauses
            - As all contexts are singletons and have no key fields, get_key method is not required
        """
        return StubContext

    base_field: str = "abc"
    """Field of the base class."""

