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
from typing import Sequence
from typing import TypeGuard

_INVALID_FILENAME_SYMBOLS = r'/\\<>:"|?*\x00\n'
"""Invalid filename symbols."""

_INVALID_FILENAME_RE = re.compile(f"[{_INVALID_FILENAME_SYMBOLS}]")
"""Precompiled regex to check for invalid filename symbols."""

_INVALID_PATH_SYMBOLS = r'<>:"|?*\x00\n'
"""Precompiled regex to check for invalid filename symbols."""

_INVALID_PATH_RE = re.compile(f"[{_INVALID_PATH_SYMBOLS}]")
"""Precompiled regex to check for invalid filename symbols."""


class FileUtil:
    """Utilities for working with files."""

    @classmethod
    def enumerate_files(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> tuple[str]:
        """
        Return the list of absolute file paths under the specified directories with the specified extension.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "json" or "csv")
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        # Return empty list if no dirs are specified in settings
        if not dirs:
            return tuple()

        # Normalize dirs to remove redundant slash at the end
        dirs = tuple(os.path.normpath(x) for x in dirs)

        # Add dot prefix from ext if not included
        ext = f".{ext}" if not ext.startswith(".") else ext

        # Walk through the directory tree for each specified preload dir
        result = []
        for dir in dirs:
            for dir_path, dir_names, filenames in os.walk(dir):

                # Apply the file include patterns
                if file_include_patterns is not None:
                    filenames = [x for x in filenames if any(fnmatch(x, y) for y in file_include_patterns)]

                # Apply the file exclude patterns
                if file_exclude_patterns is not None:
                    filenames = [x for x in filenames if not any(fnmatch(x, y) for y in file_exclude_patterns)]

                # Append the files that satisfy both patterns to the result
                dir_name = os.path.basename(dir_path)
                if not dir_name.startswith("."):
                    # Add files with extension ext except from a dot-prefixed directory
                    result.extend(os.path.normpath(os.path.join(dir_path, f)) for f in filenames if f.endswith(ext))

                # Modify list in place to exclude dot-prefixed directories
                dir_names[:] = [d for d in dir_names if not d.startswith(".")]

        return tuple(result)

    @classmethod
    def guard_valid_filename(cls, filename: str, *, raise_on_fail: bool = True) -> TypeGuard[str]:
        """Check if invalid symbols are present in filename (do not use for path with directory separators)."""
        if not _INVALID_FILENAME_RE.search(filename):
            return True
        elif raise_on_fail:
            # Raise on fail
            raise RuntimeError(
                f"Filename '{filename}' is not valid because it contains special characters "
                f"from this list: '{_INVALID_FILENAME_SYMBOLS}'"
            )
        else:
            # Return False on fail
            return False

    @classmethod
    def guard_valid_path(cls, path: str, *, raise_on_fail: bool = True) -> TypeGuard[str]:
        """Check if invalid symbols are present in directory or file path (directory separators are allowed)."""
        if not _INVALID_PATH_RE.search(path):
            return True
        elif raise_on_fail:
            # Raise on fail
            raise RuntimeError(
                f"Directory or file path '{path}' is not valid because it contains special characters "
                f"from this list: '{_INVALID_PATH_SYMBOLS}'"
            )

        else:
            # Return False on fail
            return False

    @classmethod
    def has_extension(cls, path: str, ext: str | None) -> bool:
        """Return True if filename or path extension matches argument, use ext=None to return True for any extension."""
        # Get the actual extension from path
        actual_ext = os.path.splitext(path)[1]

        # Normalize both
        ext = cls.normalize_ext(ext)
        actual_ext = cls.normalize_ext(actual_ext)

        # Check for match
        return actual_ext == ext

    @classmethod
    def check_extension(cls, path: str, ext: str | None) -> None:
        """Error if filename or path extension does not match argument, use ext=None to check for any extension."""
        if not cls.has_extension(path, ext):
            # Get the actual extension from path
            actual_ext = os.path.splitext(path)[1]

            # Normalize both
            ext = cls.normalize_ext(ext)
            actual_ext = cls.normalize_ext(actual_ext)

            # Report error
            if ext is not None:
                if actual_ext is not None:
                    raise RuntimeError(
                        f"Filename or path '{path}' has extension '{actual_ext}' which does not match "
                        f"the expected extension '{ext}'."
                    )
                else:
                    raise RuntimeError(
                        f"Filename or path '{path}' has no extension while extension '{ext}' should be present."
                    )
            else:
                raise RuntimeError(
                    f"Filename or path '{path}' has extension '{actual_ext}' while no extension should be present."
                )

    @classmethod
    def normalize_ext(cls, ext: str) -> str | None:
        """Remove leading period if specified and convert to lowercase."""
        # Check for None or empty string
        if ext is not None and ext != "":
            result = ext[1:] if ext.startswith(".") else ext
            result = result.lower()
            return result
        else:
            return None
