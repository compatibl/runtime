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
from cl.runtime.db.filter import Filter
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename


@dataclass(slots=True, kw_only=True)
class FilterMany(Filter):
    """Selects records with the specified keys."""

    keys: list[KeyMixin] = required()
    """The filter selects records with the specified keys."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Perform checks to ensure all keys list elements are keys, and all have the same key type
        assert TypeCheck.guard_key_sequence(self.keys)
        if self.keys:
            key_type = type(self.keys[0])
            mismatched_types = [typename(type(key)) for key in self.keys if type(key) != key_type]
            if mismatched_types:
                mismatched_types_str = ", ".join(mismatched_types)
                raise RuntimeError(f"Keys in FilterMany have more than one type: {mismatched_types_str}")
        else:
            raise RuntimeError(f"FilterMany must have at least one key.")

        # Set key_type_name in this class based on the key type of self.keys
        self.key_type_name = typename(key_type)
