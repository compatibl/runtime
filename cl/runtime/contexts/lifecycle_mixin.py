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

from abc import abstractmethod
from typing_extensions import Self
from cl.runtime.records.type_util import TypeUtil


class LifecycleMixin:
    """Provides a common interface for resource initialization and disposal using a 'with' clause."""

    __entered: bool | None = None
    """Set to true after __enter__ is invoked and cannot be unset."""

    __exited: bool | None = None
    """Set to true after __exit__ is invoked and cannot be unset."""

    @abstractmethod
    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        if self.__entered:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.__enter__ is called twice, which may happen\n"
                f"when the same instance is used in two nested 'with' clauses.")
        if self.__exited:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.__enter__ is called after __exit__, which may happen\n"
                f"when the same instance is used in two separate 'with' clauses.")
        self.__entered = True

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        if not self.__entered:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.__exit__ is called before __enter__, which may happen\n"
                f"when the same instance is used in two interleaved 'with' clauses.")
        if self.__exited:
            raise RuntimeError(
                f"{TypeUtil.name(self)}.__exit__ is called twice, which may happen\n"
                f"when the same instance is used in two interleaved 'with' clauses.")
        self.__exited = True

    def _check_lifecycle_phase(self) -> None:
        """Check that __enter__ has been invoked but __exit__ has not."""
        if not self.__entered:
            raise RuntimeError(f"{TypeUtil.name(self)} is used outside of a 'with' clause.")
        if self.__exited:
            raise RuntimeError(f"{TypeUtil.name(self)} is used after exit from a 'with' clause.")
