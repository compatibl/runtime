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

from typing import cast
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_key_type, is_record_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typenameof
from cl.runtime.records.typename import typeof


class KeyUtil:
    """Helper methods for key types."""

    @classmethod
    def is_equal(cls, obj: KeyMixin, other: KeyMixin) -> bool:
        """Compare keys when arguments are keys or records."""
        obj_key = cast(RecordMixin, obj).get_key() if is_record_type(type(obj)) else obj
        other_key = cast(RecordMixin, other).get_key() if is_record_type(type(other)) else other
        return obj_key == other_key

    @classmethod
    def get_hash(cls, key: KeyMixin) -> int:
        """Get hash for key types only, error if not a key type or not frozen."""
        if is_key_type(typeof(key)):
            if key.is_frozen():
                # Invoke hash for each field to call hash recursively for the inner key fields of composite keys
                return hash(tuple(hash(getattr(key, field_name)) for field_name in key.get_field_names()))
            else:
                raise RuntimeError(f"Cannot hash an instance of {typenameof(key)} because it is not frozen.")
        else:
            raise RuntimeError(f"Cannot hash an instance of {typeof(key)} because it is not a key.")
