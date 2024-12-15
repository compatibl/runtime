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
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Type
from typing_extensions import Self
from cl.runtime.records.dataclass_freezable import DataclassFreezable
from cl.runtime.records.record_util import RecordUtil

_DEFAULT_DICT: Dict = {}
"""Default extensions are created based on settings and are shared by all asynchronous contexts."""

_DEFAULT_CONTEXT_LOCK = threading.Lock()
"""Thread lock for the default context."""


@dataclass(slots=True, kw_only=True)
class ExtensionContext(DataclassFreezable):
    """Base class extension contexts in the 'extensions' field of the main context class Context."""

    @classmethod
    @abstractmethod
    def get_extension_category(cls) -> Type:
        """Return base class of each extension category even if called from a derived class."""

    @classmethod
    @abstractmethod
    def create_default(cls) -> Self:
        """Create default context for the extension category returned by 'get_extension_category' method."""

    @classmethod
    def _default(cls) -> Self:
        """
        Return the default extension context instance for this type, or create and cache it if does not exist.
        This method is safe to call from different asynchronous environments (threads or asyncio tasks).
        """

        # First check without a lock to avoid the overhead of acquiring the lock if the value already exists
        global _DEFAULT_DICT
        extension_category = cls.get_extension_category()
        # First check is readonly, no lock required
        if (result := _DEFAULT_DICT.get(extension_category, None)) is None:
            # If not found, try to create
            created_extension = cls.create_default()
            created_extension_category = created_extension.get_extension_category()
            if not isinstance(created_extension, cls):
                raise RuntimeError(
                    f"Default extension has type {type(created_extension).__name__} which is not a"
                    f"subclass of the requested extension type {cls.__name__}.")
            if not isinstance(created_extension, created_extension_category):
                raise RuntimeError(
                    f"Default extension has type {type(created_extension).__name__} which is not a"
                    f"subclass of its own extension category {created_extension_category.__name__}.")
            RecordUtil.init_all(created_extension)
            with _DEFAULT_CONTEXT_LOCK:
                # Use setdefault to ensure the value is not created between the first and second check
                result = _DEFAULT_DICT.setdefault(extension_category, created_extension)
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
                raise RuntimeError(
                    f"Duplicate extension context type(s) found in {where_msg}:\n" f"{duplicate_type_names}\n"
                )
