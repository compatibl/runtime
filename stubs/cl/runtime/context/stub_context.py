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
from typing import Type
from typing_extensions import Self
from cl.runtime.context.base_context import BaseContext


@dataclass(slots=True, kw_only=True)
class StubContext(BaseContext):
    """Stub context."""

    stub_context_id: str = "abc"
    """Stub context identifier."""

    error_on_post_init: bool = False
    """If True, an error will be raised inside '__post_init__' method for testing purposes."""

    error_on_init: bool = False
    """If True, an error will be raised inside 'init' method (not __init__) for testing purposes."""

    error_on_enter: bool = False
    """If True, an error will be raised inside __enter__ method for testing purposes."""

    error_on_exit: bool = False
    """If True, an error will be raised inside __exit__ method for testing purposes."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "StubContext"

    def __post_init__(self):
        """Runs after __init__."""

        if self.error_on_post_init:
            raise RuntimeError("StubContext.error_on_post_init is set.")

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        if self.error_on_init:
            raise RuntimeError("StubContext.error_on_init is set.")

        # Return self to enable method chaining
        return self

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource disposal."""

        # Call __enter__ method of base class
        BaseContext.__enter__(self)

        try:
            if self.error_on_enter:
                raise RuntimeError("StubContext.error_on_enter is set.")
        except Exception as e:
            # Treat the exception as though it happened outside the 'with' clause:
            #   - Call __exit__ method of base class without passing exception details
            #   - Then rethrow the exception
            BaseContext.__exit__(self, None, None, None)
            raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Supports 'with' operator for resource disposal."""

        try:
            if self.error_on_exit:
                raise RuntimeError("StubContext.error_on_exit is set.")
        except Exception as e:
            # Treat the exception as though it happened outside the 'with' clause:
            #   - Call __exit__ method of base class without passing exception details
            #   - Then rethrow the exception
            BaseContext.__exit__(self, None, None, None)
            raise e
        else:
            # Otherwise delegate to the __exit__ method of base
            return BaseContext.__exit__(self, exc_type, exc_val, exc_tb)
