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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.views.record_view import RecordView
from cl.runtime.views.view import View


@dataclass(slots=True, kw_only=True)
class KeyView(View):
    """Generic key, record is loaded and displayed."""

    key: KeyMixin = required()
    """Generic key, record is loaded and displayed."""

    def materialize(self) -> RecordView:
        """Load record and return RecordView object. KeyView is used only for storage in the DB."""
        # TODO: Fix cast
        record = active(DataSource).load_one_or_none(self.key) if self.key else None
        return RecordView(view_for=self.view_for, view_name=self.view_name, record=record)
