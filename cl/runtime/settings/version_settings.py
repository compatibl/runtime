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
from typing_extensions import final
from cl.runtime.records.typename import typenameof
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class VersionSettings(Settings):
    """Version settings."""

    version_format_check: bool = True
    """Skip version format check if false."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if not isinstance(self.version_format_check, bool):
            raise RuntimeError(
                f"Field version_format_check must be of type bool but has type {typenameof(self.version_format_check)}."
            )
