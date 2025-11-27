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
from dataclasses import dataclass
from types import FunctionType, NoneType
from types import MethodType
from typing import Iterable
from typing import get_type_hints
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.handler_param_decl import HandlerParamDecl
from cl.runtime.schema.handler_variable_decl import HandlerVariableDecl


@dataclass(slots=True, kw_only=True)
class HandlerDeclareBlockDecl(DataclassMixin):
    """Handler declaration block in type declaration."""

    handlers: list[HandlerDeclareDecl] = required()
    """Handler declaration data."""

    @classmethod
    def get_type_methods(cls, record_type: type, inherit: bool = False) -> "HandlerDeclareBlockDecl":
        """Extract class public methods."""

        handlers: list[HandlerDeclareDecl] = []
        type_members: Iterable[str] = dir(record_type) if inherit else vars(record_type)

        # Search for methods in type members
        for member_name in type_members:

            # Skip private and protected methods
            if member_name.startswith("_"):
                continue

            member = getattr(record_type, member_name)
            if not (inspect.isfunction(member) or inspect.ismethod(member)):
                continue

            handler_type = cls._get_handler_type_by_name(member_name)
            if handler_type is None:
                continue

            handler = cls._build_handler_declaration(record_type, member_name, member, handler_type)
            handlers.append(handler)

        return cls(handlers=handlers)

    @classmethod
    def _get_handler_type_by_name(cls, name: str) -> str | None:
        """Get handler type by method name prefix."""
        if name.startswith("run_"):
            return "Job"
        if name.startswith("view_"):
            return "Viewer"
        return None

    @classmethod
    def _build_handler_declaration(
        cls, record_type: type, member_name: str, member: FunctionType | MethodType, handler_type: str
    ) -> HandlerDeclareDecl:
        """Build HandlerDeclareDecl object from properties."""
        handler = HandlerDeclareDecl()
        handler.name = CaseUtil.snake_to_pascal_case(member_name)
        handler.comment = member.__doc__
        handler.static = (
            # The handler is considered static if it is declared as staticmethod or classmethod.
            # It does not matter if it is a classmethod or staticmethod from UI perspective
            # (they are both considered static)
            isinstance(inspect.getattr_static(record_type, member_name), (staticmethod, classmethod))
        )

        handler.label = cls._get_handler_label(member_name)
        handler.type_ = handler_type

        # Add schema info about handler parameters
        if params := cls.get_method_params(member):
            handler.params = params

        # Process method's return type
        # TODO: Add support of return comment
        # TODO (Roman): Consider the differentiation between no return annotation and None return annotation.
        if (return_type := cls._get_return_type(member)) not in (None, NoneType):
            handler.return_ = HandlerVariableDecl.create(value_type=return_type, record_type=record_type)

        return handler

    @classmethod
    def _get_return_type(cls, member: FunctionType | MethodType) -> type | None:
        """Get return type from method signature."""
        func = member.__func__ if isinstance(member, MethodType) else member

        try:
            hints = get_type_hints(func)
        except Exception:
            return None

        return hints.get("return")

    @classmethod
    def _get_handler_label(cls, member_name: str) -> str:
        """Get handler label by removing 'view_' and 'run_' prefix from method name and converting to Title case."""
        result = member_name.removeprefix("view_")
        result = result.removeprefix("run_")
        return CaseUtil.snake_to_title_case(result)

    @classmethod
    def get_method_params(cls, method: FunctionType | MethodType) -> list[HandlerParamDecl]:
        """Extract parameters from a given method"""
        params: list[HandlerParamDecl] = []

        func = method.__func__ if isinstance(method, MethodType) else method

        try:
            type_hints = get_type_hints(func)
        except Exception:
            # In case of any resolution issues, fall back to raw annotations
            type_hints = {}

        method_signature = inspect.signature(method)
        method_params = method_signature.parameters
        for param_name, param in method_params.items():
            if param_name in {"self", "cls"}:
                continue

            # Prefer resolved type from get_type_hints, fall back to raw annotation
            annotation = type_hints.get(param_name, param.annotation)

            if annotation is inspect.Signature.empty:
                continue

            variable_decl = HandlerVariableDecl.create(annotation, annotation)
            param_decl = HandlerParamDecl.create(
                name=CaseUtil.snake_to_pascal_case(param_name),
                variable_decl=variable_decl,
            )
            params.append(param_decl)

        return params
