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


class VersionUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    def guard_version_string(cls, ver: str, *, raise_on_fail: bool = True) -> bool:
        """Check that the version string matches the CompatibL Platform CalVer format."""
        tokens = ver.split(".")
        is_valid = (
            len(tokens) == 3 and
            all(p.isdigit() and (p == '0' or not p.startswith('0')) for p in tokens)
            and 25 <= int(tokens[0]) <= 999  # Two-digit year from 2025 to 2999
            and 101 <= int(tokens[1]) <= 1231  # Month and day combined from 101 (Jan 1) to 1231 (Dec 31)
        )
        if is_valid:
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Version string {ver} does not follow the CompatibL Platform\n"
                               f"CalVar convention of YY.MDD.PATCH. Examples:\n"
                               f" - 23.101.0 for Jan 1, 2023 release\n"
                               f" - 23.501.1 for patch 1 to May 1, 2023 release\n")
        else:
            return False
