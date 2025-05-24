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
from fnmatch import fnmatch
from typing import List

from cl.runtime.csv_util import CsvUtil
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.project_settings import ProjectSettings


def check_csv_preloads(
    *,
    include_patterns: List[str] | None = None,
    exclude_patterns: List[str] | None = None,
    apply_fix: bool,
    verbose: bool = False,
) -> None:
    """
    Check csv preload files in all subdirectories of 'root_path' to ensure that each field that
    is a number or date is surrounded by double quotes ". This will prevent Excel modifying
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
                file_path = str(os.path.join(dir_path, filename))
                is_modified = CsvUtil.check_file(file_path, apply_fix=apply_fix)
                if is_modified:
                    files_with_error.append(file_path)

    if files_with_error:
        files_list = "".join([f"    {file}\n" for file in files_with_error])
        msg = f"Found fields that should be wrapped in the following CSV preload(s):\n{files_list}"
        if not apply_fix:
            raise RuntimeError(msg)
        elif verbose:
            print(msg)
    elif verbose:
        files_list = "".join([f"    {x}\n" for x in sorted(all_root_paths)])
        print(f"Verified field wrapping in the following CSV preload(s):\n{files_list}")
