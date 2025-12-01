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
from dataclasses import dataclass
from typing_extensions import final
from cl.runtime.configs.config import Config
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.file_util import FileUtil
from cl.runtime.prebuild.csv_file_util import CsvFileUtil
from cl.runtime.records.typename import typename
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class PreloadSettings(Settings):
    """Settings for preloading records from files."""

    preload_dirs: list[str] | None = None
    """
    Absolute or relative (to Dynaconf project root) directory paths under which preloaded data is located.
    
    Notes:
        - Each element of 'dir_path' will be searched for csv, yaml, and json subdirectories
        - For CSV, the data is in csv/.../ClassName.csv where ... is optional dataset
        - For YAML, the data is in yaml/ClassName/.../KeyToken1;KeyToken2.yaml where ... is optional dataset
        - For JSON, the data is in json/ClassName/.../KeyToken1;KeyToken2.json where ... is optional dataset
    """

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Convert to absolute paths if specified as relative paths and convert to list if single value is specified
        self.preload_dirs = ProjectSettings.instance().normalize_paths("dirs", self.preload_dirs)

    def save_and_configure(self, *, record_types: list[type] | None = None) -> None:
        """Save records from preload directory to DB and execute run_configure on all preloaded Config records."""

        # Load records from files
        records = CsvFileUtil.load_all(dirs=self.preload_dirs, record_types=record_types)

        if records:
            # Insert to database
            active(DataSource).insert_many(records, commit=True)

            # Execute run_config on all preloaded Config records
            config_records = [record for record in records if isinstance(record, Config)]
            tuple(config_record.run_configure() for config_record in config_records)


