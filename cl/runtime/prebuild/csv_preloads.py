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
import csv
import re
from fnmatch import fnmatch
from dateutil.parser import parse
from typing import List
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.project_settings import ProjectSettings

def should_wrap(value: str) -> bool:
    """Return True if the value begins from [{ or is a number or date and is not already wrapped in triple quotes."""
    if value.startswith('"""'):
        # Do not modify if already at least three quotes at start
        return False
    else:
        # Strip whitespace first and then any existing quotes
        value = value.strip()
        value = value.strip('"')
        if value and value[0] in ("[", "{"):
            # Begins from [ or {
            return True
        elif re.fullmatch(r"\d+(\.\d+)?%?", value):
            # Numbers and percentages Excel will interpret as numeric
            return True
        else:
            # Try parsing as date (including with words like "March", "Dec", etc.)
            try:
                parse(value, fuzzy=False)
                return True
            except Exception:  # noqa
                return False


def wrap_special_values(file_path: str):
    """Read a CSV file, wrap values if they should be wrapped, and return true if the file was modified."""

    is_modified = False
    updated_rows = []
    with open(file_path, 'r', newline='', encoding='utf-8') as input_file:
        reader = csv.reader(input_file)
        for row in reader:
            new_row = []
            for value in row:
                if should_wrap(value):
                    is_modified = True
                    value = value.strip('"')
                    wrapped_val = f'"""{value} """'
                    new_row.append(wrapped_val)
                else:
                    new_row.append(value)
            updated_rows.append(new_row)

    # Overwrite only if modified
    if is_modified:
        with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.writer(output_file, quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writerows(updated_rows)
    return is_modified


def check_csv_preloads(
    *,
    include_patterns: List[str] | None = None,
    exclude_patterns: List[str] | None = None,
    apply_fix: bool,
    verbose: bool = False,
) -> None:
    """
    Check csv preload files in all subdirectories of 'root_path' to ensure that each field that
    begins from [{ or is a number or date is surrounded by double quotes ". This will prevent Excel modifying
    these fields on save (e.g., using locale-specific format for dates) or triggering JSON loading.

    Args:
        include_patterns: Optional list of filename glob patterns to include, use the defaults in code if not specified
        exclude_patterns: Optional list of filename glob patterns to exclude, use the defaults in code if not specified
        apply_fix: If True, modify CSV so each field containing numbers or symbols is surrounded by quotes
        verbose: Print messages about fixes to stdout if specified
    """

    # The list of packages from context settings
    packages = ContextSettings.instance().packages

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
    if include_patterns is None:
        include_patterns = ["*.csv"]

    # Use default exclude patterns if not specified by the caller
    if exclude_patterns is None:
        exclude_patterns = []

    # Apply to each element of root_paths
    files_with_error = []
    for root_path in all_root_paths:
        # Walk the directory tree
        for dir_path, dir_names, filenames in os.walk(root_path):
            # Apply exclude patterns
            filenames = [x for x in filenames if not any(fnmatch(x, y) for y in exclude_patterns)]

            # Apply include patterns
            filenames = [x for x in filenames if any(fnmatch(x, y) for y in include_patterns)]

            for filename in filenames:
                # Load the file
                file_path = os.path.join(dir_path, filename)
                is_modified = wrap_special_values(file_path)
                if is_modified:
                    files_with_error.append(file_path)

    if files_with_error:
        raise RuntimeError(
            "Field that begins from [{ or is a number or date not escaped by quotes in CSV preload(s):\n"
            + "".join([f"    {file}\n" for file in files_with_error])
        )
    elif verbose:
        print(
            "Verified CSV preloads format under directory root(s):\n"
            + "".join([f"    {x}\n" for x in sorted(all_root_paths)])
        )
