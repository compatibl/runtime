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

import locate

# Ensure package_settings module can be found
locate.append_sys_path("../..")

# Extend sys.path and PYTHONPATH with source and stubs dirs for all packages in settings.yaml
from cl.runtime.settings.package_settings import PackageSettings  # isort: skip Prevent isort from moving this line

PackageSettings.instance().configure_paths()
