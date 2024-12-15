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

import threading
from dataclasses import dataclass
from typing_extensions import Self
from typing import Dict, Type, List

from cl.runtime.records.dataclass_freezable import DataclassFreezable
from cl.runtime.records.record_util import RecordUtil

_DEFAULT_DICT: Dict = {}
"""Default extensions are created based on settings and are shared by all asynchronous contexts."""

_DEFAULT_CONTEXT_LOCK = threading.Lock()
"""Thread lock for the default context."""

@dataclass(slots=True, kw_only=True)
class ContextExtension(DataclassFreezable):
    """Base class for the defaults objects stored in Context.defaults field."""

    @classmethod
    def _default(cls) -> Self:
        """
        Return the default context extension instance for this type, or create and cache it if does not exist.
        This method is safe to call from different asynchronous environments (threads or asyncio tasks).
        """

        # First check without a lock to avoid the overhead of acquiring the lock if the value already exists
        global _DEFAULT_DICT
        if (result := _DEFAULT_DICT.get(cls, None)) is None:
            created_extension = cls()
            RecordUtil.init_all(created_extension)
            with _DEFAULT_CONTEXT_LOCK:
                # Use setdefault to ensure the value is not created between the first and second check
                result = _DEFAULT_DICT.setdefault(cls, created_extension)
        return result

    @classmethod
    def check_duplicate_types(cls, types: List[Type], where_msg: str) -> None:
        """Check for duplicate types, error message specifying duplicate types and where they were found."""
        # Fast check to see if there are duplicates
        if len(set(types)) < len(types):
            # Only if found, slower search for duplicates
            duplicate_types = set(t for t in types if types.count(t) > 1)
            if duplicate_types:
                duplicate_type_names = "\n".join(t.__name__ for t in duplicate_types)
                raise RuntimeError(f"Duplicate context extension type(s) found in {where_msg}:\n"
                                   f"{duplicate_type_names}\n")
