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
from typing import Dict
from typing import List
from pydantic import BaseModel
from pydantic import Field
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.schema.type_import import TypeImport
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.slots_util import SlotsUtil


class SelectResponse(BaseModel):
    """Response data type for the /storage/select route."""

    schema_: Dict[str, Any] = Field(..., alias="schema")
    """Schema field of the response data type for the /storage/select route."""

    data: List[Dict[str, Any]]
    """Data field of the response data type for the /storage/select route."""

    @classmethod
    def get_records(cls, request: SelectRequest) -> SelectResponse:
        """Implements /storage/select route."""

        record_type = TypeImport.from_qual_name(f"{request.module}.{request.type_}")

        # Load records for type
        records = DbContext.get_db().load_all(record_type)  # noqa

        # Serialize records for table
        serialized_records = [cls._serialize_record_for_table(record) for record in records]

        # Get schema dict for type
        type_decl_dict = TypeResponseUtil.get_type(TypeRequest(name=request.type_, module=request.module, user="root"))

        return SelectResponse(schema=type_decl_dict, data=serialized_records)

    @classmethod
    def _serialize_record_for_table(cls, record: RecordProtocol) -> Dict[str, Any]:
        """
        Serialize record to ui table format.
        Contains only fields of supported types, _key and _t will be added based on record.
        """

        all_slots = SlotsUtil.get_slots(record.__class__)

        # Get subset of slots which supported in table format
        table_fields = {
            CaseUtil.snake_to_pascal_case_keep_trailing_underscore(slot)
            for slot in all_slots
            if (slot_v := getattr(record, slot))
            and (
                # TODO (Roman): check other types for table format
                # Check if field is primitive, key or enum
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
