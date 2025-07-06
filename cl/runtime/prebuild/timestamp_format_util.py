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

import os
import re
from fnmatch import fnmatch
from typing import List
from cl.runtime.settings.app_settings import AppSettings
from cl.runtime.settings.project_settings import ProjectSettings


class TimestampFormatUtil:
    """Helper class for checking and fixing timestamp format."""

    @classmethod
    def update_text(cls, text: str) -> str:
        """Update Timestamp format in text."""
        # Pattern for the legacy format
        legacy_pattern = r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3})Z-([a-fA-F0-9]{20})"
        # Replace delimiters to match new format
        new_format = r"\1-\2-\3-\4-\5-\6-\7-\8"

        # Perform the substitution
        updated_text = re.sub(legacy_pattern, new_format, text)
        return updated_text

    @classmethod
    def update_file(cls, file_path: str) -> None:
        """Update Timestamp format in file."""
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Replace the target string with the replacement
        content = cls.update_text(content)

        # Write back to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    @classmethod
    def update_timestamps(
        cls,
        *,
        file_include_patterns: List[str] | None = None,
        file_exclude_patterns: List[str] | None = None,
    ) -> None:
        """
        Check that timestamp format is correct inside the specified files under the project root.

        Args:
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        # The list of packages from context settings
        packages = AppSettings.instance().app_packages

        missing_files = []
        all_root_paths = set()
        for package in packages:
            # Add paths to source and stubs directories
            if (x := ProjectSettings.get_source_root(package)) is not None and x not in all_root_paths:
                all_root_paths.add(x)
            if (x := ProjectSettings.get_stubs_root(package)) is not None and x not in all_root_paths:
                all_root_paths.add(x)
            if (x := ProjectSettings.get_tests_root(package)) is not None and x not in all_root_paths:
                all_root_paths.add(x)
            if (x := ProjectSettings.get_preloads_root(package)) is not None and x not in all_root_paths:
                all_root_paths.add(x)

        # Use default include patterns if not specified by the caller
        if file_include_patterns is None:
            file_include_patterns = ["*.csv", "*.txt"]

        # Use default exclude patterns if not specified by the caller
        if file_exclude_patterns is None:
            file_exclude_patterns = []

        # Apply to each element of root_paths
        files_with_error = []
        for root_path in all_root_paths:
            # Walk the directory tree
            for dir_path, dir_names, filenames in os.walk(root_path):
                # Apply exclude patterns
                filenames = [x for x in filenames if not any(fnmatch(x, y) for y in file_exclude_patterns)]
                # Apply include patterns
                filenames = [x for x in filenames if any(fnmatch(x, y) for y in file_include_patterns)]
                # Iterate over filenames
                for filename in filenames:
                    # Load the file
                    file_path = str(os.path.join(dir_path, filename))
                    TimestampFormatUtil.update_file(file_path)
