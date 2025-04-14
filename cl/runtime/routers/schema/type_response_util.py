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
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_info_cache import TypeInfoCache


class TypeResponseUtil:
    """Response helper class for the /schema/typeV2 route."""

    @classmethod
    def get_type(cls, request: TypeRequest) -> dict[str, dict]:
        """Implements /storage/get_datasets route."""

        # TODO: Check why empty module is passed, is module the short name prefix?
        record_type = TypeInfoCache.get_class_from_type_name(request.type_name)
        handler_args_elements = dict()
        result = TypeDecl.as_dict_with_dependencies(record_type)

        # TODO: Experimental patch to exclude generated fields from top grid and editor but not the record picker
        # This patch is activated in three cases:
        # - Top grid
        # - When a new record is created and the editor is opened
        # - When getting the schema for the picker, however this is excluded by endswith("Key")
        if request.type_name is not None and not request.type_name.endswith("Key"):
            type_dict = list(result.values())[0] if len(result) > 0 else None
            if type_dict is not None:
                elements = type_dict.get("Elements", None)
                if elements is not None:
                    for index, element in enumerate(elements):
                        if element.get("Name", None) in ["EntryId", "CompletionId"]:  # TODO: Replace by preloads
                            elements.pop(index)
                            break

        for decl_name, decl_dict in result.items():
            # Add Implement handlers block
            if not (declare_block := decl_dict.get("Declare")):
                continue

            if not (handlers_block := declare_block.get("Handlers")):
                continue

            # TODO (Roman): Skip abstract methods
            implement_block = [{"Name": handler_decl.get("Name")} for handler_decl in handlers_block]
            result[decl_name]["Implement"] = {"Handlers": implement_block}

            # Create schema for method arguments if so present
            for handler in handlers_block:
                if not (params := handler.get("Params")):
                    continue

                handler_args_schema_name = f"{decl_name}{handler['Name']}Args"
                handler_args_elements[handler_args_schema_name] = {"Elements": params}

        result.update(handler_args_elements)
        return result
