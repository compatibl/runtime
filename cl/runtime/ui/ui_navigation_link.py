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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin


@dataclass(slots=True, kw_only=True)
class UiNavigationLink(DataclassMixin):
    """
    Represents a reference link for frontend navigation, enabling selection of a specific record and view.

    This class provides the necessary information to construct navigation links
    in the frontend, including the type, an optional record key, and an optional view name.
    """

    type_name: str = required()
    """The type of the navigation link, indicating the target entity or section in the frontend."""

    key: KeyMixin | None = None
    """The optional record key, identifying the specific record to navigate to."""

    view_name: str | None = None
    """The optional name of the view to navigate to in the frontend. If not specified, the default view is activated."""
