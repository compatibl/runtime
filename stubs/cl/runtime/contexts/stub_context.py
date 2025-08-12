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
from typing import Self
from cl.runtime import RecordMixin
from stubs.cl.runtime.contexts.stub_context_key import StubContextKey


@dataclass(slots=True, kw_only=True)
class StubContext(StubContextKey, RecordMixin):
    """Stub context."""

    error_on_post_init: bool = False
    """If True, an error will be raised inside '__post_init__' method for testing purposes."""

    error_on_init: bool = False
    """If True, an error will be raised inside '__init' method (not __init__) for testing purposes."""

    error_on_enter: bool = False
    """If True, an error will be raised inside __enter__ method for testing purposes."""

    error_on_exit: bool = False
    """If True, an error will be raised inside __exit__ method for testing purposes."""

    def get_key(self) -> StubContextKey:
        return StubContextKey(id=self.id).build()

    def __post_init__(self):
        """Runs after __init__."""

        if self.error_on_post_init:
            raise RuntimeError("StubContext.error_on_post_init is set.")

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.error_on_init:
            raise RuntimeError("StubContext.error_on_init is set.")

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""

        if self.error_on_enter:
            raise RuntimeError("StubContext.error_on_enter is set.")

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""

        if self.error_on_exit:
            raise RuntimeError("StubContext.error_on_exit is set.")
