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
import re
from typing import Tuple

from dateutil.parser import parse


class CsvUtil:
    """Utilities for CSV serialization."""

    # Precompiled Regex, months are valid for Anglophone locales only
    _NUMERIC_RE = re.compile(r"[0-9]")
    _ALPHA_RE = re.compile(r"[A-Za-z]")
    _MONTH_RE = re.compile(
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
        r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
        re.IGNORECASE
    )

    @classmethod
    def strip_quotes(cls, value: str) -> str:
        """Strip the existing surrounding triple quotes or single quotes."""
        if value.startswith('"""') and value.endswith('"""'):
            return value[3:-3]
        elif value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        else:
            return value

    @classmethod
    def existing_quotes(cls, value: str) -> int:
        """Count the existing surrounding triple quotes or single quotes."""
        if value.startswith('"""') and value.endswith('"""'):
            return 3
        elif value.startswith('"') and value.endswith('"'):
            return 1
        else:
            return 0

    @classmethod
    def required_quotes(cls, value: str) -> int:
        """
        Return the number of surrounding quotes required to prevent Excel from reformatting the data on save.

        Returns:
          - 3 if the value contains dates or numbers
          - 1 if the value contains commas, quotes, or newlines (following RFC 4180)
          - 0 if the value does not need to be escaped
        """

        # Strip the existing surrounding triple quotes or single quotes
        value = cls.strip_quotes(value)

        # Return 3 if the value contains dates or numbers
        if cls._NUMERIC_RE.search(value):
            if not cls._ALPHA_RE.search(value):
                # No letters, return True
                return 3
            elif cls._MONTH_RE.search(value):
                # Has months, check if date parsing succeeds
                try:
                    parse(value, fuzzy=False)
                    # Recognized as a pure date
                    return 3
                except:  # noqa
                    # Not a pure date even though it has the substrings
                    pass
            else:
                # Not a pure number or date
                pass

        # Return 1 if the value contains commas, quotes, or newlines (following RFC 4180)
        if any(c in value for c in [',', '"', '\n', '\r']):
            return 1

        # Otherwise return 0
        return 0

    @classmethod
    def wrap_value(cls, value: str) -> Tuple[str, bool]:
        """Wrap value to the correct number of quotes, return (new_value, is_modified)."""

        required_quotes = cls.required_quotes(value)
        existing_quotes = cls.existing_quotes(value)
        is_modified = required_quotes != existing_quotes
        if is_modified:
            # Strip the existing surrounding triple quotes or single quotes
            value = cls.strip_quotes(value)
            if required_quotes == 3:
                pre_save_quotes = 1
            else:
                pre_save_quotes = 0
            quotes = pre_save_quotes * '"'
            new_value = f"{quotes}{value}{quotes}"
        else:
            new_value = value
        return new_value, is_modified

    @classmethod
    def check_or_fix_file(cls, file_path: str, *, apply_fix: bool) -> bool:
        """Return true if the file has values that must be wrapped, save the modified file is apply_fix is True."""

        is_modified = False
        updated_rows = []
        with open(file_path, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                if apply_fix:
                    new_row = []
                for value in row:
                    new_value, is_value_modified = cls.wrap_value(value)
                    is_modified = is_modified or is_value_modified
                    if apply_fix:
                        new_row.append(new_value)
                if apply_fix:
                    updated_rows.append(new_row)

        # Overwrite only if apply_fix is True and the data has been modified
        if apply_fix and is_modified:
            with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
                writer = csv.writer(
                    output_file,
                    delimiter=",",
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar="\\",
                    lineterminator=os.linesep,
                )
                writer.writerows(updated_rows)
        return is_modified
