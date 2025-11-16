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
from dateutil.parser import parse


class CsvUtil:
    """Utilities for CSV serialization."""

    # Precompiled Regex, months are valid for Anglophone locales only
    _NUMERIC_RE = re.compile(r"[0-9]")
    _ALPHA_RE = re.compile(r"[A-Za-z]")
    _MONTH_RE = re.compile(
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
        r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
        re.IGNORECASE,
    )

    @classmethod
    def strip_quotes(cls, value: str) -> str:
        """Strip the surrounding single quotes if present, return the argument if not present."""
        if value.startswith('"') and value.endswith('"'):
            # Only if both leading and trailing quote is present
            return value[1:-1]
        else:
            return value

    @classmethod
    def has_quotes(cls, value: str) -> bool:
        """Return True if surrounded by quotes, both leading and trailing quote must be present."""
        return value.startswith('"') and value.endswith('"')

    @classmethod
    def requires_quotes(cls, value: str) -> bool:
        """
        Return True if quotes are required to prevent Excel from reformatting the value on save, namely
        dates (including with month in words), ints, floats and percentages. The result is the same
        irrespective of whether or not the value is already surrounded by quotes.
        surrounded by quotes.
        """

        # Strip the existing surrounding quotes if present, pass through the argument if not present
        value = cls.strip_quotes(value)

        # True if the value contains dates or numbers
        if cls._NUMERIC_RE.search(value):
            if not cls._ALPHA_RE.search(value):
                # No letters, return True
                return True
            elif cls._MONTH_RE.search(value):
                # Has months, check if date parsing succeeds
                try:
                    parse(value, fuzzy=False)
                    # Recognized as a pure date
                    return True
                except:  # noqa
                    # Not a pure date even though it has month substrings, return False
                    return False
            else:
                # Not a pure number or date, return False
                return False
        else:
            # Otherwise return False
            return False

    @classmethod
    def should_wrap(cls, value: str) -> bool:
        """Return True if quotes are required but not present, False in all other cases."""
        requires_quotes = cls.requires_quotes(value)
        has_quotes = cls.has_quotes(value)
        result = requires_quotes and not has_quotes
        return result

    @classmethod
    def check_or_fix_quotes(cls, file_path: str, *, apply_fix: bool) -> bool:
        """Return true if the file has values that must be wrapped, save the modified file is apply_fix is True."""

        is_valid = True
        updated_rows = []
        with open(file_path, "r", newline="", encoding="utf-8") as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                updated_row = []
                for value in row:
                    # Valid only if none of the values should be wrapped
                    should_wrap = cls.should_wrap(value)
                    wrapped_value = f'"{value}"' if should_wrap else value
                    # Do not wrap lists or dicts stored as strings
                    if wrapped_value and wrapped_value.startswith('"['):  # TODO: ! Add dict exclusion
                        wrapped_value = wrapped_value[1:]
                    if wrapped_value and wrapped_value.endswith(']"'):  # TODO: ! Add dict exclusion
                        wrapped_value = wrapped_value[:-1]
                    is_valid = wrapped_value == value
                    updated_row.append(wrapped_value)
                updated_rows.append(updated_row)

        # Overwrite only if apply_fix is True and is_valid is False
        if apply_fix and not is_valid:
            with open(file_path, "w", newline="", encoding="utf-8") as output_file:
                writer = csv.writer(
                    output_file,
                    delimiter=",",
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar="\\",
                    lineterminator=os.linesep,
                )
                writer.writerows(updated_rows)
        return is_valid
