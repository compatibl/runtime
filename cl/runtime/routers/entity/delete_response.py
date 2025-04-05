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
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED


class DeleteResponse(BaseModel):
    """Data type for the /entity/delete_many response."""

    @classmethod
    def get_response(cls, request: DeleteRequest) -> "DeleteResponse":
        """Delete entities."""
        class_dict = TypeSchema.get_class_dict()

        record_key_dicts = [key.model_dump() for key in request.record_keys]
        key_type_hints = [TypeHint.for_class(key.__class__) for key in request.record_keys]
        deserialized_record_keys = [
            _KEY_SERIALIZER.deserialize(
                key["_key"],
                TypeHint.for_class(TypeSchema.for_type_name(key["_t"]).get_class()),
            )
            for key in record_key_dicts
        ]
        DbContext.delete_many(deserialized_record_keys, dataset=request.dataset)

        return DeleteResponse()
