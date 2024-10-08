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
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Type
from cl.runtime import Context
from cl.runtime.file.reader import Reader
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.serialization.flat_dict_serializer import FlatDictSerializer

serializer = FlatDictSerializer()


@dataclass(slots=True, kw_only=True)
class CsvFileReader(Reader):
    """Load records from a single CSV file into the context data source."""

    record_type: Type
    """Absolute path to the CSV file including extension."""

    file_path: str
    """Absolute path to the CSV file including extension."""

    def read(self) -> None:
        # Get current context
        context = Context.current()

        with open(self.file_path, mode="r", encoding="utf-8") as file:
            # The reader is an iterable of row dicts
            csv_reader = csv.DictReader(file)

            # Deserialize rows into records
            records = [self._deserialize_row(row_dict) for row_dict in csv_reader]

            # Save records to the specified data source
            if records:
                context.save_many(records)

    def _deserialize_row(self, row_dict: Dict[str, Any]) -> RecordProtocol:
        """Deserialize row into a record."""

        prepared_row = {}
        for k, v in row_dict.items():

            # TODO (Roman): add ability to see difference between an empty string and None.
            # Replace empty string to None
            if v is None or v == "":
                prepared_row[k] = None
                continue

            # Try to convert value from csv to int or float
            try:
                prepared_row[k] = int(v)
            except ValueError:
                try:
                    prepared_row[k] = float(v)
                except ValueError:
                    prepared_row[k] = v

        prepared_row["_type"] = self.record_type.__name__
        return serializer.deserialize_data(prepared_row)
