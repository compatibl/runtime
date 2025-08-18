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

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.save_request import SaveRequest
from cl.runtime.serializers.data_serializers import DataSerializers

_UI_SERIALIZER = DataSerializers.FOR_UI


class SaveResponseUtil:
    """Util class for /storage/save route implementation."""

    @classmethod
    def save_records(cls, request: SaveRequest) -> list[KeyRequestItem]:

        # Handle empty request.
        if not request.records:
            return []

        # TODO (Roman): Align UiTypeState data model and UiTypeState dict from ui.
        # Skip saving UiTypeState objects.
        if request.records[0].get("_t") == "UiTypeState":
            return [KeyRequestItem(key="", type="") for _ in range(len(request.records))]

        deserialized_records = tuple(_UI_SERIALIZER.deserialize(record_dict) for record_dict in request.records)

        # Check if all received records are of the same key type.
        first_key_type = deserialized_records[0].get_key_type()
        if not all(record.get_key_type() == first_key_type for record in deserialized_records):
            raise RuntimeError("Bulk save records of different key types currently is not supported.")

        # Save records to DB.
        active(DataSource).replace_many(deserialized_records, commit=True)

        # Create KeyRequestItem objects of saved records for response.
        saved_key_items = [KeyRequestItem.from_key_or_record(record) for record in deserialized_records]
        return saved_key_items
