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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.schema.type_decl_key import TypeDeclKey
from cl.runtime.ui.user_key import UserKey


@dataclass(slots=True)
class UiTypeStateKey(KeyMixin):
    """Defines some default settings for a type."""

    type_: TypeDeclKey = required()
    """Type reference."""

    user: UserKey = required()
    """A user the app state is applied for."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return UiTypeStateKey
