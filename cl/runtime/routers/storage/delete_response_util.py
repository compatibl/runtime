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
from cl.runtime.routers.storage.delete_request import DeleteRequest
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED


class DeleteResponseUtil:
    """Util class for /storage/delete route implementation."""

    @classmethod
    def delete_records(cls, request: DeleteRequest) -> list[KeyRequestItem]:
        """Delete records by keys."""

        # Handle empty request.
        if not request.delete_keys:
            return request.delete_keys

        # TODO (Roman): Consider allowing different key types in a single delete request.
        #  If different key types are prohibited then the delete request model should be simplified.
        # Check if all requested keys are of the same key type.
        if not all(key_item.type == request.delete_keys[0].type for key_item in request.delete_keys):
            raise RuntimeError("Bulk delete records of different key types currently is not supported.")

        # Expect all keys to be the same key type.
        key_type = TypeCache.from_type_name(request.delete_keys[0].type).get_key_type()  # noqa
        key_type_hint = TypeHint.for_type(key_type)  # noqa

        # Deserialize keys in request.
        deserialized_keys = tuple(
            _KEY_SERIALIZER.deserialize(key_item.key, key_type_hint).build()
            for key_item in request.delete_keys or tuple()
        )

        # Delete records.
        active(DataSource).delete_many(deserialized_keys, commit=True)

        return request.delete_keys
