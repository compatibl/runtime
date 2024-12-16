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
from abc import abstractmethod
from typing import Type


class ContextMixin(ABC):
    """Optional mixin class for a context, code must not rely on inheritance from this class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    @abstractmethod
    def get_key_type(cls) -> Type:
        """
        To get the current context for cls, ContextManager will perform dict lookup based cls.get_key_type().

        Notes:
            - Return as specific type rather than type(self) to avoid variation across derived types
            - The returned type may be a base context class or a dedicated key type
            - Contexts that have different key types are isolated from each other and have independent 'with' clauses
            - As all contexts are singletons and have no key fields, get_key method is not required
        """
