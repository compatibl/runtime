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
from cl.runtime.routers.entity.delete_request import DeleteRequest
from cl.runtime.serializers.dict_serializer import get_type_dict
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.ui_dict_serializer import UiDictSerializer

data_serializer = UiDictSerializer()
_KEY_SERIALIZER = KeySerializers.DEFAULT


class DeleteResponse(BaseModel):
    """Data type for the /entity/delete_many response."""

    @classmethod
    def get_response(cls, request: DeleteRequest) -> "DeleteResponse":
        """Delete entities."""
        type_dict = get_type_dict()

        record_key_dicts = [key.model_dump() for key in request.record_keys]
        deserialized_record_keys = [
            _KEY_SERIALIZER.deserialize(key["_key"], type_dict[key["_t"]])
            for key in record_key_dicts
        ]
        DbContext.delete_many(deserialized_record_keys, dataset=request.dataset)

        return DeleteResponse()
