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
from dataclasses import dataclass
from typing import Any
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.reader import Reader
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.serializers.data_serializers import DataSerializers

_SERIALIZER = DataSerializers.FOR_CSV


@dataclass(slots=True, kw_only=True)
class CsvFileReader(Reader):
    """Load records from a single CSV file into the context database."""

    file_path: str
    """Absolute path to the CSV file including extension."""

    def csv_to_db(self) -> None:
        # Get current context

        with open(self.file_path, mode="r", encoding="utf-8") as file:
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
                    f"Misaligned values found in the following rows of CSV file: {self.file_path}\n"
                    f"Check the placement of commas and double quotes.\n" + rows_str
                )

            # Deserialize rows into records
            records = [self._deserialize_row(row_dict) for row_dict in row_dicts]

            # Save records to the specified database
            if records:
                active(DataSource).save_many(records)

    def _deserialize_row(self, row_dict: dict[str, Any]) -> RecordProtocol:
        """Deserialize row into a record."""

        # Record type is ClassName without extension in PascalCase
        filename = os.path.basename(self.file_path)
        filename_without_extension, _ = os.path.splitext(filename)

        if not CaseUtil.is_pascal_case(filename_without_extension):
            dirname = os.path.dirname(filename)
            raise RuntimeError(
                f"Filename of a CSV preload file {filename} in directory {dirname} must be "
                f"ClassName or its alias in PascalCase without module."
            )

        # Get record type
        record_type = TypeCache.get_class_from_type_name(filename_without_extension)

        # Normalize chars and set None for empty strings
        row_dict = {CharUtil.normalize(k): CharUtil.normalize_or_none(v) for k, v in row_dict.items()}
        row_dict["_type"] = TypeUtil.name(record_type)

        result = _SERIALIZER.deserialize(row_dict).build()
        return result
