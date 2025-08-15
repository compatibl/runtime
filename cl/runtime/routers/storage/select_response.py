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
from typing import Any
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.storage.records_with_schema_response import RecordsWithSchemaResponse
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers


class SelectResponse(RecordsWithSchemaResponse):
    """Response data type for the /storage/select route."""

    @classmethod
    def get_response(cls, request: SelectRequest) -> SelectResponse:
        """Implements /storage/select route."""

        if request.query_dict:
            raise RuntimeError("Select with 'query_dict' currently is not supported.")

        if request.table_format is False:
            raise RuntimeError("Select with 'table_format=False' currently is not supported.")

        if request.skip != 0:
            raise RuntimeError("Select with 'skip != 0' currently is not supported.")

        if request.limit is not None:
            raise RuntimeError("Select with 'limit' currently is not supported.")

        ds = active(DataSource)

        # TODO(Roman): !!! Implement separate methods for table and type
        if TypeCache.is_type(type_name=request.type_, type_kind=TypeKind.RECORD):
            # Get records for a type
            record_type_name = request.type_
            record_type = TypeCache.from_type_name(record_type_name)
            # Load records for the type
            records = ds.load_type(record_type)
            common_base_record_type = record_type
        else:
            # Get records for a table
            key_type_name = request.type_
            key_type = TypeCache.from_type_name(key_type_name)
            records = ds.load_all(key_type)
            # Get lowest common type to the records stored in the table
            common_base_record_type_name = ds.get_common_base_record_type_name(key_type_name=key_type_name)
            common_base_record_type = TypeCache.from_type_name(common_base_record_type_name)

        # Serialize records for table.
        serialized_records = [cls._serialize_record_for_table(record) for record in records]

        # Get schema dict for type.
        schema_dict = cls._get_schema_dict(common_base_record_type)

        return SelectResponse(schema_=schema_dict, data=serialized_records)  # noqa

    @classmethod
    def _serialize_record_for_table(cls, record: RecordProtocol) -> dict[str, Any]:
        """
        Serialize record to ui table format.
        Contains only fields of supported types, _key and _t will be added based on record.
        """

        all_slots = record.get_field_names()

        # Get subset of slots which supported in table format.
        table_fields = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(slot)
            for slot in all_slots
            if (slot_v := getattr(record, slot))
            and (
                # TODO (Roman): Consider adding other types to table format.
                # Check if field is primitive, key or enum.
                slot_v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                or is_key(slot_v)
                or isinstance(slot_v, Enum)
            )
        }

        # Serialize record to ui format and filter table fields
        table_dict = {k: v for k, v in DataSerializers.FOR_UI.serialize(record).items() if k in table_fields}

        # Add "_t" and "_key" attributes
        table_dict["_t"] = TypeUtil.name(record)
        table_dict["_key"] = KeySerializers.DELIMITED.serialize(record.get_key())

        return table_dict
