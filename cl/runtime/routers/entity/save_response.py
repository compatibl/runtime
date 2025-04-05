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

from pydantic import BaseModel
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.routers.entity.save_request import SaveRequest
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


class SaveResponse(BaseModel):
    """Data type for the /entity/save response."""

    key: str | None
    """String representation of the key for the saved record."""

    class Config:
        populate_by_name = True

    @classmethod
    def _save_entity(cls, request: SaveRequest) -> "SaveResponse":
        """Save entity."""

        # Get ui record and apply ui conversion
        ui_record = request.record_dict

        # TODO (Roman): align UiTypeState data model and UiTypeState dict from ui
        # Skip saving UiTypeState object
        if ui_record.get("_t") == "UiTypeState":
            return SaveResponse(key=None)

        # Deserialize record
        record = _UI_SERIALIZER.deserialize(ui_record)
        record_key = record.get_key()
        record_key_str = _KEY_SERIALIZER.serialize(record_key)
        DbContext.save_one(record, dataset=request.dataset)

        return SaveResponse(key=record_key_str)

    @classmethod
    def get_response(cls, request: SaveRequest) -> "SaveResponse":
        return cls._save_entity(request)
