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

from cl.runtime.file.csv_reader import CsvReader
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.settings.env_settings import EnvSettings

if __name__ == '__main__':

    # The list of packages from context settings
    packages = EnvSettings.instance().env_packages

    dirs = set()
    for package in packages:
        # Add paths to source and stubs directories
        if (x := ProjectLayout.get_source_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_stubs_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_tests_root(package)) is not None and x not in dirs:
            dirs.add(x)
        if (x := ProjectLayout.get_preloads_root(package)) is not None and x not in dirs:
            dirs.add(x)

    # Create __init__.py files in subdirectories except for tests
    CsvReader.check_or_fix_quotes(
        dirs=tuple(dirs),
        ext="csv",
        apply_fix=True,
        verbose=True,
        # Prevent fixing of the unit test samples
        file_exclude_patterns=[
            "unescaped_date.csv",
            "unescaped_float.csv",
        ]
    )
