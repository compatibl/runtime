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

from typing import Sequence
from packaging.requirements import Requirement


class ProjectChecks:
    """Checks for project settings."""

    @classmethod
    def guard_requirement(cls, req: str, *, raise_on_fail: bool = True) -> bool:
        """Confirm that a single requirement has valid format."""
        try:
            # Parses PEP 508 requirement strings
            Requirement(req)
            return True
        except Exception:  # noqa
            if raise_on_fail:
                raise RuntimeError(f"Requirement {req} has invalid format.")
            else:
                return False

    @classmethod
    def guard_requirements(cls, reqs: Sequence[str], *, raise_on_fail: bool = True) -> bool:
        """Confirm that all requirements have valid format."""
        # Function all returns True when the sequence is empty
        return all(cls.guard_requirement(req, raise_on_fail=raise_on_fail) for req in reqs)
