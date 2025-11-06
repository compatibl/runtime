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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class ColumnState(DataclassMixin):
    """Column specific settings."""

    id: str = None
    """Column ID."""

    filter: str | None = None
    """Column   The maximum possible item size in pixels."""

    hidden: bool | None = None
    """Hidden column flag."""

    sort_desc: bool | None = None
    """Column soring order."""

    size_in_percent: float | None = None
    """Item size in percent."""

    max_size_in_pixels: float | None = None
    """The maximum possible item size in pixels."""

    min_size_in_pixels: float | None = None
    """The minimum possible item size in pixels."""

    size_fixed: bool | None = None
    """Indicates if the size of an item cannot be modified in runtime."""
