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

from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.key_mixin import KeyMixin
from dataclasses import dataclass
from typing import Type


@dataclass(slots=True, kw_only=True)
class ContextKey(KeyMixin):
    """Polymorphic data storage with dataset isolation."""

    context_id: str = missing()
    """Context identifier will be set to data_source.data_source_id in __post_init__ if not specified."""

    @classmethod
    def get_key_type(cls) -> Type:
        return ContextKey