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
from dataclasses import dataclass, field
from typing import Dict
from typing import List
from cl.runtime.schema.field_spec import FieldSpec
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class DataSpec(TypeSpec, ABC):
    """Provides information about a class with fields."""

    fields: List[FieldSpec] | None = None
    """Fields in class declaration order."""

    _field_dict: Dict[str, FieldSpec] | None = None
    """Dictionary of field specs indexed by field name."""

    def get_field_dict(self) -> Dict[str, FieldSpec]:
        """Dictionary of field specs indexed by field name."""
        if self._field_dict is None:
            self._field_dict = {x.field_name: x for x in self.fields} if self.fields is not None else {}
        return self._field_dict
