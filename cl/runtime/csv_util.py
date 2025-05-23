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
        re.IGNORECASE
    )
    @classmethod
    def should_wrap(cls, value: str) -> bool:
        """Return True if Excel will reformat the value on save (e.g., for numbers or dates)."""

        # Check if already properly wrapped in triple quotes
        if not value or (value.startswith('"""') and value.endswith('"""')):
            # Do not modify if None, empty, or already wrapped in triple quotes
            return False

        # Remove leading and trailing quotes
        value = value.strip().strip('"')

        # Wrap if purely numeric (or percent-formatted) string that either has no letters at all, or has months
        if cls._NUMERIC_RE.search(value):
            x = bool(cls._MONTH_RE.search(value, re.IGNORECASE))
            y = bool(cls._ALPHA_RE.search(value))
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
                    # Not a pure date even though it has the substrings
                    return False
            else:
                # Not a pure number or date, return False
                return False

        # Do not wrap if none of the above criteria are met
        return False

    @classmethod
    def wrap_string(cls, value: str) -> str:
        """Wrap only if should_wrap returns True."""
        if cls.should_wrap(value):
            value = value.strip('"')
            result = f'"""{value}"""'
            return result
        else:
            return value

    @classmethod
    def check_file(cls, file_path: str, *, apply_fix: bool) -> bool:
        """Return true if the file has values that must be wrapped, save the modified file is apply_fix is True."""

        is_modified = False
        updated_rows = []
        with open(file_path, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                if apply_fix:
                    new_row = []
                for value in row:
                    if cls.should_wrap(value):
                        is_modified = True
                        value = value.strip('"')
                        wrapped_val = f'"""{value}"""'
                        if apply_fix:
                            new_row.append(wrapped_val)
                    else:
                        if apply_fix:
                            new_row.append(value)
                if apply_fix:
                    updated_rows.append(new_row)

        # Overwrite only if apply_fix is True and the data has been modified
        if apply_fix and is_modified:
            with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
                for row in updated_rows:
                    line = ','.join(value for value in row)
                    output_file.write(line + '\n')
        return is_modified
