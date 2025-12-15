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

import pytest

from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.frontend_settings import FrontendSettings


def test_version_conventions():
    """Prebuild test to that the version strings comply with CompatibL CalVer conventions."""

    # Check package versions
    packages = EnvSettings.instance().env_packages
    dirs = [ProjectLayout.get_package_root(package=package) for package in packages]
    version_files = FileUtil.enumerate_files(
        dirs=dirs,
        file_include_patterns="_version.py",
    )
    # TODO(Roman): Implement using VersionUtil check

    # Check frontend version in settings.yaml, creating the instance performs version validation
    FrontendSettings.instance()


if __name__ == "__main__":
    pytest.main([__file__])
