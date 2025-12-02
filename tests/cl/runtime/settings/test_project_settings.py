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
import os
from pathlib import Path
from cl.runtime.file.project_layout import ProjectLayout


def test_project_settings():
    """Test ProjectLayout class."""

    # Relative to the location of this test module
    two_level_root_dir = os.path.normpath(Path(__file__).parents[5])
    one_level_root_dir = os.path.normpath(Path(__file__).parents[4])

    # Check project root
    if (project_levels := ProjectLayout.get_project_levels()) == 1:
        assert ProjectLayout.get_project_root() == one_level_root_dir
        assert ProjectLayout.get_package_root("cl.runtime") == ProjectLayout.get_project_root()
        assert ProjectLayout.get_source_root("cl.runtime") == os.path.normpath(
            os.path.join(ProjectLayout.get_project_root(), "cl", "runtime")
        )
    elif project_levels == 2:
        assert ProjectLayout.get_project_root() == two_level_root_dir
        assert ProjectLayout.get_package_root("cl.runtime") == os.path.normpath(
            os.path.join(ProjectLayout.get_project_root(), "runtime")
        )
        assert ProjectLayout.get_source_root("cl.runtime") == os.path.normpath(
            os.path.join(ProjectLayout.get_project_root(), "runtime", "cl", "runtime")
        )
    else:
        raise RuntimeError(f"The number of project levels {project_levels} is not 1 or 2.")


if __name__ == "__main__":
    pytest.main([__file__])
