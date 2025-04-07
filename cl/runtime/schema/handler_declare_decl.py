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
from typing import List
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.handler_param_decl import HandlerParamDecl
from cl.runtime.schema.handler_variable_decl import HandlerVariableDecl


@dataclass(slots=True, kw_only=True)
class HandlerDeclareDecl:
    """Handler declaration data."""

    name: str = required()
    """Handler name."""

    label: str | None = None
    """Handler label."""

    comment: str | None = None
    """Handler comment."""

    type_: str = required()  # TODO: Rename to handler_type for clarity
    """Handler type."""

    params: List[HandlerParamDecl] | None = None
    """Handler parameters."""

    return_: HandlerVariableDecl | None = None
    """Handler return value."""

    static: bool | None = None
    """If set as true, handler will be static, otherwise non-static."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.type_ not in (
            handler_types := [
                "job",  # Job handler is shown as a button, return type must be None, params are allowed
                "process",  # Process handler, return type is not allowed, params are allowed
                "viewer",  # Viewer, return type is allowed, params are allowed
                "content",  # # Viewer, return type is allowed, params not allowed
            ]
        ):
            raise RuntimeError(
                f"Field TypeDecl.type_ has the value of {self.type_}\n"
                f"Permitted values are {', '.join(handler_types)}"
            )
