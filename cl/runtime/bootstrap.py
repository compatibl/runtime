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

import importlib
import os
import sys
from pathlib import Path

# Extend PYTHONPATH to include cl.runtime package source
try:
    # Try to import package_settings module dynamically
    module = importlib.import_module("cl.runtime.settings.package_settings")
except ImportError as e:
    runtime_path = str(Path(__file__).resolve().parents[2])
    print(f"Adding cl.runtime source to PYTHONPATH: {runtime_path}")
    # Update sys.path for the current running process
    sys.path.append(runtime_path)
    # Update os.environ["PYTHONPATH"] for any future subprocesses
    if current_pythonpath := os.environ.get("PYTHONPATH", ""):
        # Append to the existing PYTHONPATH
        os.environ["PYTHONPATH"] = current_pythonpath + os.pathsep + runtime_path
    else:
        # Initialize PYTHONPATH if not present
        os.environ["PYTHONPATH"] = runtime_path

# Extent PYTHONPATH to include all other package sources and stubs
from cl.runtime.settings.package_settings import PackageSettings

PackageSettings.instance().configure_pythonpath()
