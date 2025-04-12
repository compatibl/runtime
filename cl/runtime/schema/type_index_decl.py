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
from typing import List
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.index_decl import IndexDecl


@dataclass(slots=True, kw_only=True)
class TypeIndexDecl(Data):
    """Type index declaration."""

    name: str | None = None
    """Index name."""

    elements: List[IndexDecl] = required()
    """Index elements."""
