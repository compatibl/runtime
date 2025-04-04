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

from __future__ import annotations
from pydantic import BaseModel
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED


class KeyRequestItem(BaseModel):
    """Class for single key information."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    key: str
    """Key string in semicolon-delimited format."""

    type: str
    """Key type name."""

    @classmethod
    def from_record_or_key(cls, record_or_key) -> KeyRequestItem:
        """Create KeyRequestItem from record or key."""

        if is_record(record_or_key):
            key = record_or_key.get_key()
        elif is_key(record_or_key):
            key = record_or_key
        else:
            raise RuntimeError(f"The object {str(record_or_key)}) is neither a record nor a key.")

        key_ = _KEY_SERIALIZER.serialize(key)
        type_ = TypeUtil.name(key)

        return cls(key=key_, type=type_)
