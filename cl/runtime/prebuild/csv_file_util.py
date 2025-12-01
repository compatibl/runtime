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

import csv
import os
from fnmatch import fnmatch
from typing import Any
from typing import Sequence
from cl.runtime.csv_util import CsvUtil
from cl.runtime.file.file_util import FileUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.project_settings import ProjectSettings

_SERIALIZER = DataSerializers.FOR_CSV


class CsvFileUtil:
    """Helper class for working with CSV files."""

    @classmethod
    def load_all(
        cls,
        *,
        dirs: Sequence[str],
        ext: str = "csv",
        record_types: Sequence[type] | None = None,
    ) -> tuple[RecordMixin]:
        """Load records from CSV files with the specified extension in the specified directory."""

        # Enumerate files in the specified directories
        file_paths = FileUtil.enumerate_files(dirs=dirs, ext=ext)

        # Restrict to specified final record types if provided
        if record_types is not None:
            # Limit to the specified final record types
            record_type_names = [typename(record_type) for record_type in record_types]
            file_paths = [
                file_path for file_path in file_paths if os.path.basename(file_path).split(".")[0] in record_type_names
            ]

        # Iterate over files
        result = []
        for file_path in file_paths:

            # Record type is ClassName without extension in PascalCase
            filename = os.path.basename(file_path)
            filename_without_extension, _ = os.path.splitext(filename)

            if not CaseUtil.is_pascal_case(filename_without_extension):
                dirname = os.path.dirname(filename)
                raise RuntimeError(
                    f"Filename of a CSV preload file {filename} in directory {dirname} must be "
                    f"ClassName or its alias in PascalCase without module."
                )

            # Get record type
            record_type = TypeInfo.from_type_name(filename_without_extension)

            with open(file_path, mode="r", encoding="utf-8") as file:

                # The reader is an iterable of row dicts
                csv_reader = csv.DictReader(file)
                row_dicts = [row_dict for row_dict in csv_reader]

                invalid_rows = set(
                    index
                    for index, row_dict in enumerate(row_dicts)
                    for key in row_dict.keys()
                    if key is None or key == ""  # TODO: Add other checks for invalid keys
                )

                if invalid_rows:
                    rows_str = "".join([f"Row: {invalid_row}\n" for invalid_row in invalid_rows])
                    raise RuntimeError(
                        f"Misaligned values found in the following rows of CSV file: {file_path}\n"
                        f"Check the placement of commas and double quotes.\n" + rows_str
                    )

                # Deserialize rows into records and add to the result
                loaded = [cls._deserialize_row(record_type=record_type, row_dict=row_dict) for row_dict in row_dicts]
                result.extend(loaded)

        # Convert to tuple and return
        return tuple(result)

    @classmethod
    def check_or_fix_quotes(
        cls,
        *,
        apply_fix: bool,
        verbose: bool = False,
        file_include_patterns: list[str] | None = None,
        file_exclude_patterns: list[str] | None = None,
    ) -> None:
        """
        Check csv preload files in all subdirectories of 'root_path' to ensure that each field that
        is a number or date is surrounded by triple quotes in the CSV file (single quotes if opened in Excel).
        This will prevent Excel modifying these fields on save (e.g., using locale-specific format for dates)
        or triggering JSON loading.

        Args:
            apply_fix: If True, modify CSV so each field containing numbers or symbols is surrounded by quotes
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        # The list of packages from context settings
        packages = EnvSettings.instance().env_packages

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
            file_include_patterns = ["*.csv"]

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
                    is_valid = CsvUtil.check_or_fix_quotes(file_path, apply_fix=apply_fix)
                    if not is_valid:
                        files_with_error.append(file_path)

        if files_with_error:
            files_list = "".join([f"    {file}\n" for file in files_with_error])
            msg = (
                f"Found values that should be wrapped in quotes to stop Excel from modifying them on save.\n"
                f"Run fix_csv_quotes script to fix. CSV preload file(s) that have this error:\n{files_list}"
            )
            if not apply_fix:
                raise RuntimeError(msg)
            elif verbose:
                print(msg)
        elif verbose:
            files_list = "".join([f"    {x}\n" for x in sorted(all_root_paths)])
            print(f"Verified field wrapping in the following CSV preload(s):\n{files_list}")

    @classmethod
    def _deserialize_row(cls, *, record_type: type, row_dict: dict[str, Any]) -> RecordMixin:
        """Deserialize row into a record."""

        # Normalize chars and set None for empty strings
        row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}
        row_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(row_dict).build()
        return result
