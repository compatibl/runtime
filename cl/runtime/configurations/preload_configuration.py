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

from dataclasses import dataclass
from itertools import chain
from typing import Sequence

from more_itertools import consume
from typing_extensions import final
from cl.runtime.configurations.configuration import Configuration
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.preload_settings import PreloadSettings


@dataclass(slots=True, kw_only=True)
@final
class PreloadConfiguration(Configuration):
    """Settings for preloading records from files."""

    dirs: Sequence[str] | None = None
    """Directories where file search is performed."""

    file_include_patterns: Sequence[str] | None = None
    """Optional list of filename glob patterns to include."""

    file_exclude_patterns: Sequence[str] | None = None
    """Optional list of filename glob patterns to exclude"""

    def run_configure(self):
        """Load records from files in the specified directories and insert them into the active data source."""

        # Ensure that DB in the active data source is empty, not considering parents
        if not (ds := active(DataSource)).is_empty(consider_parents=False):
            raise RuntimeError(
                f"PreloadConfiguration requires an empty DB in the active data source (not considering parents),\n"
                f"but found that DB '{ds.get_db_id()}' is not empty."
            )

        # Use preload_dirs if dirs field is None
        preload_settings = PreloadSettings.instance()
        dirs = self.dirs or preload_settings.preload_dirs

        # Specify readers for each file extension
        reader_dict = {
            "csv": CsvReader().build(),
        }

        # Get records stored in preload directories
        record_lists = [
            reader.load_all(
                dirs=dirs,
                ext=ext,
                file_include_patterns=self.file_include_patterns,
                file_exclude_patterns=self.file_exclude_patterns,
            )
            for ext, reader in reader_dict.items()
        ]

        # Chain records into a single list
        records = list(chain(*record_lists))

        if records:
            # Insert into the active data source
            ds.insert_many(records, commit=True)

            # Execute run_configure on all preloaded Configuration records with autorun=True
            autorun_configurations = [
                record for record in records
                if isinstance(record, Configuration) and record.autorun
            ]

            # Execute their run_configure methods
            consume(autorun_configuration.run_configure() for autorun_configuration in autorun_configurations)

