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
from typing import Any
from typing import Sequence
from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.csv_util import CsvUtil
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_CSV


class CsvReader(Reader):
    """Helper class for working with CSV files."""

    def load_all(
        self,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> tuple[RecordMixin]:

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        # Iterate over files
        result = []
        for file_path in file_paths:
            try:
                # Determine record type from filename
                record_type = FileUtil.get_type_from_filename(file_path)

                with open(file_path, mode="r", encoding="utf-8") as file:

                    # The reader is an iterable of row dicts
                    csv_reader = csv.DictReader(file)
                    row_dicts = [row_dict for row_dict in csv_reader]

                    invalid_rows = {
                        index
                        for index, row_dict in enumerate(row_dicts)
                        for key in row_dict.keys()
                        if key is None or key == ""  # TODO: Add other checks for invalid keys
                    }

                    if invalid_rows:
                        rows_str = "".join([f"Row: {invalid_row}\n" for invalid_row in invalid_rows])
                        raise RuntimeError(
                            "Misaligned values found in the following rows.\n"
                            "Check the placement of commas and double quotes.\n" + rows_str
                        )

                    # Deserialize rows into records and add to the result
                    loaded = [self._deserialize_row(record_type=record_type, row_dict=row_dict) for row_dict in row_dicts]
                    result.extend(loaded)
            except Exception as e:
                raise RuntimeError(f"Failed to load CSV file {file_path}. Error: {e}") from e

        # Convert to tuple and return
        return tuple(result)

    @classmethod
    def check_or_fix_quotes(
        cls,
        *,
        dirs: Sequence[str],
        ext: str,
        apply_fix: bool,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """
        Check csv preload files in all subdirectories of 'root_path' to ensure that each field that
        is a number or date is surrounded by triple quotes in the CSV file (single quotes if opened in Excel).
        This will prevent Excel modifying these fields on save (e.g., using locale-specific format for dates)
        or triggering JSON loading.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "csv")
            apply_fix: If True, modify CSV so each field containing numbers or symbols is surrounded by quotes
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """

        # Enumerate files in the specified directories, taking into account include and exclude patterns
        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        # Iterate over filenames
        files_with_error = []
        for file_path in file_paths:
            # Load the file
            is_valid = CsvUtil.check_or_fix_quotes(file_path, apply_fix=apply_fix)
            if not is_valid:
                files_with_error.append(file_path)

        if files_with_error:
            files_list = "".join([f"    {file}\n" for file in files_with_error])
            msg = (
                f"Found values that should be wrapped in quotes to stop Excel from modifying them on save.\n"
                f"RECOMMENDED ACTION: Run fix_csv_quotes script to fix.\n{files_list}"
            )
            if not apply_fix:
                raise RuntimeError(msg)
            elif verbose:
                print(msg)
        elif verbose:
            files_list = "".join([f"    {x}\n" for x in sorted(file_paths)])
            print(f"Verified field wrapping in the following CSV preload files:\n{files_list}")

    @classmethod
    def _deserialize_row(cls, *, record_type: type, row_dict: dict[str, Any]) -> RecordMixin:
        """Deserialize row into a record.
        Args:
            record_type: Type of the record to deserialize into
            row_dict: Dictionary representing a CSV row
        Returns:
            Deserialized record
        Raises:
            RuntimeError: If deserialization fails
        """

        # Normalize chars and set None for empty strings
        row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}
        row_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(row_dict).build()
        return result
