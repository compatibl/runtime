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
from enum import Enum
from typing import Dict
from typing import Type
from memoization import cached
from typing_extensions import Self
from cl.runtime.schema.type_import import TypeImport
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_decl_key import TypeDeclKey


class Schema:
    """
    Provide declarations for the specified type and all dependencies.
    """

    @classmethod
    @cached
    def for_type(cls, record_type: Type) -> Dict[str, Dict]:
        """
        Declarations for the specified type and all dependencies, returned as a dictionary.

        Args:
            record_type: Type of the record for which the schema is created.
        """
        dependencies = set()

        # Get or create type declaration the argument class
        type_decl_obj = TypeDecl.for_type(record_type, dependencies=dependencies)

        # Sort the list of dependencies
        dependencies = sorted(dependencies, key=lambda x: TypeUtil.name(x))

        # TODO: Restore after Enum decl generation is supported
        dependencies = [dependency_type for dependency_type in dependencies if not issubclass(dependency_type, Enum)]

        # Requested type is always first
        type_decl_list = [type_decl_obj] + [TypeDecl.for_type(dependency_type) for dependency_type in dependencies]

        # TODO: Move pascalize to a helper class
        result = {
            f"{type_decl.module.module_name}.{type_decl.name}": type_decl.to_type_decl_dict()
            for type_decl in type_decl_list
        }
        return result
