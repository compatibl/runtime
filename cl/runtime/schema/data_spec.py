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

from abc import ABC
from dataclasses import dataclass
from typing import Dict
from typing import List
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.field_spec import FieldSpec
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class DataSpec(TypeSpec, ABC):
    """Provides information about a class with fields."""

    fields: List[FieldSpec] | None = None
    """Fields in class declaration order."""

    _field_dict: Dict[str, FieldSpec] = required()
    """Dictionary of field specs indexed by field name."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self._field_dict = {field.field_name: field for field in self.fields} if self.fields is not None else {}

    def get_field_dict(self) -> Dict[str, FieldSpec]:
        """Dictionary of field specs indexed by field name."""
        return self._field_dict
