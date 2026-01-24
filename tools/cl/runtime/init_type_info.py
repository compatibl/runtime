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

import locate  # isort: skip Prevent isort from moving this line

# Ensure bootstrap module can be found
locate.append_sys_path("../../..")

# Import bootstrap module first to configure PYTHONPATH and other settings
import cl.runtime.bootstrap  # isort: skip Prevent isort from moving this line

from cl.runtime.prebuild.init_file_util import InitFileUtil
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.settings.package_settings import PackageSettings


def init_type_info() -> None:
    """Create __init__.py files to avoid missing directories and rebuild type cache."""

    # Create __init__.py files first to avoid missing classes in directories without __init__.py
    print("Adding __init__.py files if any are missing...")
    InitFileUtil.check_init_files(apply_fix=True, verbose=False)

    # Rebuild type cache and save TypeInfo.csv file to the bootstrap resources directory
    print("Initializing the type cache...")
    packages = PackageSettings.instance().get_packages()
    TypeInfo.rebuild(packages=packages)


if __name__ == '__main__':

    # Initialize type cache
    init_type_info()
