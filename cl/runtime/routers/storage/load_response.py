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

from cl.runtime import TypeImport
from cl.runtime.backend.core.ui_type_state import UiTypeState
from cl.runtime.backend.core.ui_type_state_key import UiTypeStateKey
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.records_with_schema_response import RecordsWithSchemaResponse
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


class LoadResponse(RecordsWithSchemaResponse):
    """Response data type for the /storage/load route."""

    @classmethod
    def get_response(cls, request: LoadRequest) -> LoadResponse:

        # Handle empty request.
        if not request.load_keys:
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa

        # TODO (Roman): Consider allowing different key types in a single load request.
        #  If different key types are prohibited then the load request model should be simplified.
        # Check if all requested keys are of the same key type.
        first_key_item_type = request.load_keys[0].type
        if not all(key_item.type == first_key_item_type for key_item in request.load_keys):
            raise RuntimeError("Bulk load records of different key types currently is not supported.")

        # Expect all keys to be the same key type.
        key_type = TypeImport.class_from_type_name(first_key_item_type).get_key_type()  # noqa
        key_type_hint = TypeHint.for_class(key_type, optional=True)

        # Deserialize keys in request.
        deserialized_keys = tuple(
            _KEY_SERIALIZER.deserialize(key_item.key, key_type_hint).build() for key_item in request.load_keys or tuple()
        )

        # TODO (Yauheni): Remove temporary workaround of pinning handlers for all requested types.
        # Pin all handlers by default.
        if key_type == UiTypeStateKey:
            loaded_records = []
            for deserialized_key in deserialized_keys:
                record = DbContext.load_one_or_none(key_type, deserialized_key)

                # If record not found set default.
                if record is None:
                    record = cls._get_default_ui_type_state(deserialized_key)

                loaded_records.append(record)
        else:
            # Load record using current context, filter None values.
            loaded_records = tuple(x for x in DbContext.load_many(key_type, deserialized_keys) if x is not None)

        # TODO (Roman): Improve check for not found.
        if not request.ignore_not_found and len(loaded_records) != len(request.load_keys):
            raise RuntimeError(
                f"Not all records were found. Requested {len(request.load_keys)} keys, found {len(loaded_records)} records."
            )

        # Return empty response if records not found.
        if not loaded_records:
            return LoadResponse(schema_=cls._get_schema_dict(None), data=[])  # noqa

        # TODO (Roman): Merge schema for all types.
        # Check if all loaded records are of the same type.
        # Subtypes are also not allowed due to not implemented schema merging.
        first_record_type = type(loaded_records[0])
        if not all(type(record) == first_record_type for record in loaded_records):
            raise RuntimeError("Bulk load records of different types currently is not supported.")

        # Create schema dict by real type of the first loaded record.
        schema_dict = cls._get_schema_dict(first_record_type)

        # Serialize records.
        serialized_records = [_UI_SERIALIZER.serialize(record) for record in loaded_records]

        return LoadResponse(schema_=schema_dict, data=serialized_records)  # noqa

    @classmethod
    def _get_default_ui_type_state(cls, ui_type_state_requested_key: UiTypeStateKey) -> UiTypeState:
        """Return default UiTypeState with pinned all handlers."""

        type_state_record_type = TypeImport.class_from_type_name(ui_type_state_requested_key.type_.name)
        type_state_record_type_schema = TypeDecl.for_type_with_dependencies(type_state_record_type)

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
