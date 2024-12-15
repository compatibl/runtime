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

from typing_extensions import Self

from cl.runtime.context.extension_context import ExtensionContext
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class StubBaseExtensionContext(ExtensionContext):
    """Base extension context."""

    base_field: str = "abc"
    """Field of the base class."""
    
    @classmethod
    def get_extension_category(cls) -> Type:
        """Return base class of each extension category even if called from a derived class."""
        return StubBaseExtensionContext

    @classmethod
    def create_default(cls) -> Self:
        """Create default context for the extension category returned by 'get_extension_category' method."""
        return StubBaseExtensionContext(base_field="default")
