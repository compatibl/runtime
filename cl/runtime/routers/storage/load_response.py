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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.records_with_schema_response import RecordsWithSchemaResponse
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.ui.ui_type_state import UiTypeState
from cl.runtime.ui.ui_type_state_key import UiTypeStateKey

_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


class LoadResponse(RecordsWithSchemaResponse):
    """Response data type for the /storage/load route."""

    @classmethod
    def get_response(cls, request: LoadRequest) -> LoadResponse:

        # TODO: !!! Consider returning the same size of result as the input

        # Handle empty request
        if not request.load_keys:
            # TODO: Review and avoid noqa
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa

        # TODO: !!! Do not rely on first element to detect type
        record_type_name = request.load_keys[0].type
        record_type = TypeInfo.from_type_name(record_type_name)
        key_type = record_type.get_key_type()

        # Deserialize keys in request
        keys = tuple(
            _KEY_SERIALIZER.deserialize(x.key, TypeHint.for_type(key_type)).build()
            for x in request.load_keys or tuple()
        )

        # Load and serialize records
        loaded_records = active(DataSource).load_many_or_none(keys)

        # Find the lowest common base of the loaded types except None
        loaded_record_types = tuple(type(x) for x in loaded_records if x is not None)

        # TODO: Decide if this is the right logic to return empty response if records not found
        if loaded_record_types:
            # At least one of the records is not None
            serialized_records = [_UI_SERIALIZER.serialize(record) for record in loaded_records]

            # Find a common base
            common_base = TypeInfo.get_common_base_type(types=loaded_record_types)

            # Create schema dict for the common base
            schema_dict = cls._get_schema_dict(common_base)

            # Return data and schema
            return LoadResponse(schema_=schema_dict, data=serialized_records)  # noqa  # TODO: Review noqa
        else:
            # All of the records are None, return an empty list
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa  # TODO: Review noqa

    @classmethod
    def _get_default_ui_type_state(cls, ui_type_state_requested_key: UiTypeStateKey) -> UiTypeState:
        """Return default UiTypeState with pinned all handlers."""

        type_state_record_type = TypeInfo.from_type_name(ui_type_state_requested_key.type_.name)
        type_state_record_type_schema = TypeDecl.as_dict_with_dependencies(type_state_record_type)

        # Iterate over type declarations to get all handlers
        all_handlers = []
        for decl_dict in type_state_record_type_schema.values():
            declare_block = decl_dict.get("Declare")
            if not declare_block:
                continue

            handlers_block = declare_block.get("Handlers")
            if not handlers_block:
                continue

            all_handlers.extend(
                [
                    handler_name
                    for handler_decl in handlers_block
                    if (handler_name := handler_decl.get("Name")) not in all_handlers
                ]
            )

        return UiTypeState(
            user=ui_type_state_requested_key.user,
            type_=ui_type_state_requested_key.type_,
            pinned_handlers=all_handlers,
        )
