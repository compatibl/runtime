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

import inspect
from abc import ABC
from dataclasses import dataclass
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, init=False)
class TypeQuery(QueryMixin):
    """
    Select all records of target_type and its subtypes.
    
    Notes:
        Error if target_type defines custom tables by overriding get_table, use load_where in this case.
    """

    _target_type: type[KeyMixin] = required()

    def __init__(self, target_type: type[KeyMixin]):
        # Check that target_type does not override get_table
        if "get_table" in target_type.__dict__:
            target_type_name = TypeUtil.name(target_type)
            raise RuntimeError(
                f"Cannot create TypeQuery from {target_type_name} because it defines custom tables\n"
                f"by overriding get_table, use load_where for this type instead.")
        self._target_type = target_type

    def get_target_type(self) -> type[KeyMixin]:
        """The query will return only the subtypes of this type (each derived query must override)."""
        return self._target_type
