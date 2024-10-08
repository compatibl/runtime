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
from typing import Iterable
from typing import List
from typing import Tuple
from cl.runtime.settings.settings import Settings


def check_copyright_headers(
    *,
    source_dirs: List[str] | None = None,
    copyright_header: str | None = None,
    include_patterns: List[str] | None = None,
    exclude_patterns: List[str] | None = None,
    fix_trailing_blank_line: bool = False,
    verbose: bool = False,
) -> None:
    """
    Check that the specified copyright header is present and followed by a blank line in all files with
    the specified glob filename pattern.

    Args:
        source_dirs: Directories under which files will be checked
        copyright_header: Optional copyright header, defaults to project contributors Apache header
        include_patterns: Optional list of filename glob patterns to include, use the defaults in code if not specified
        exclude_patterns: Optional list of filename glob patterns to exclude, use the defaults in code if not specified
        fix_trailing_blank_line: If specified, add a trailing blank line after the copyright header if missing
        verbose: Print messages about fixes to stdout if specified
    """

    if source_dirs is None:
        # Default to checking namespace 'cl'
        source_dirs = ["cl/", "stubs/cl/", "tests/cl"]

    # Project root assuming the script is located in project_root/scripts
    project_root = Settings.get_project_root()

    # Absolute paths to source directories
    root_paths = [os.path.normpath(os.path.join(project_root, source_dir)) for source_dir in source_dirs]

    # Use the project contributors Apache header if not specified by the caller
    if copyright_header is None:
        copyright_header = """# Copyright (C) 2023-present The Project Contributors
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
"""
    # Use default include patterns if not specified by the caller
    if include_patterns is None:
        include_patterns = ["*.py"]

    # Use default exclude patterns if not specified by the caller
    if exclude_patterns is None:
        exclude_patterns = ["__init__.py"]

    files_with_copyright_header_error = []
    files_with_trailing_line_error = []

    # Apply to each element of root_paths
    for root_path in root_paths:
        # Walk the directory tree
        for dir_path, dir_names, filenames in os.walk(root_path):
            # Apply exclude patterns
            filenames = [x for x in filenames if not any(fnmatch(x, y) for y in exclude_patterns)]

            # Apply include patterns
            filenames = [x for x in filenames if any(fnmatch(x, y) for y in include_patterns)]

            for filename in filenames:
                # Load the file
                file_path = os.path.join(dir_path, filename)
                remaining_lines = None
                with open(file_path, "r") as file:
                    # Check for the correct copyright header (disregard the trailing blank line)
                    file_header = file.read(len(copyright_header))
                    if file_header != copyright_header:
                        # Add to the list of results if it does not start from the copyright header
                        files_with_copyright_header_error.append(str(file_path))
                    else:
                        # Otherwise check if trailing blank line is present
                        # Read the next line and check if it is a blank line or it consists only of whitespace
                        next_line = file.readline()
                        if next_line.strip(" ") != "\n":
                            # Add to the list for information purposes even if the error will be fixed
                            files_with_trailing_line_error.append(str(file_path))
                            if fix_trailing_blank_line:
                                # Read the remaining lines only if the error is being fixed
                                remaining_lines = file.readlines()

                if remaining_lines is not None:
                    # Combine the copyright header with trailing blank line with
                    # 'next_line' and 'remaining_lines' and write back to the file
                    updated_text = copyright_header + "\n" + next_line + "".join(remaining_lines)
                    with open(file_path, "w") as file:
                        file.write(updated_text)

    if files_with_copyright_header_error:
        raise RuntimeError(
            "Invalid copyright header in file(s):\n"
            + "".join([f"    {file}\n" for file in files_with_copyright_header_error])
        )
    elif files_with_trailing_line_error:
        files_with_trailing_line_msg = "missing blank line(s) after copyright header in file(s):\n" + "".join(
            [f"    {file}\n" for file in files_with_trailing_line_error]
        )
        if not fix_trailing_blank_line:
            raise RuntimeError(f"Found {files_with_trailing_line_msg}")
        elif verbose:
            print(f"Fixed {files_with_trailing_line_msg}")
    elif verbose:
        print(
            "Verified copyright header and trailing blank line under directory root(s):\n"
            + "".join([f"    {root_path}\n" for root_path in root_paths])
        )
