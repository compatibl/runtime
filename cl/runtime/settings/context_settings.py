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
from typing import Tuple
from typing_extensions import final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class ContextSettings(Settings):
    """Default context parameters."""

    packages: Tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Convert to tuple
        # TODO: Move to TupleUtil class
        if self.packages is None:
            raise RuntimeError(f"No packages are specified in {TypeUtil.name(self)}, specify at least one.")
        elif isinstance(self.packages, tuple):
            pass
        elif hasattr(self.packages, "__iter__"):
            # Convert all iterable types other than tuple itself to tuple
            self.packages = tuple(self.packages)
        elif isinstance(self.packages, str):
            # Convert string to tuple
            self.packages = (self.packages,)
        else:
            raise RuntimeError(f"Field '{TypeUtil.name(self)}.packages' must be a string or an iterable of strings.")

        # Check that each element is a string
        if package_errors := [
            (
                f"Element at index {index} of field '{TypeUtil.name(self)}.packages is not a string:\n"
                f"Value: {element} Type: {TypeUtil.name(element)})\n"
                if not isinstance(element, str)
                else f"Element at index {index} of field '{TypeUtil.name(self)} is an empty string.\n"
            )
            for index, element in enumerate(self.packages)
            if not isinstance(element, str) or element == ""
        ]:
            raise ValueError("".join(package_errors))

