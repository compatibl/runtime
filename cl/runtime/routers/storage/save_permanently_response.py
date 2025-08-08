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

from collections import defaultdict
from pathlib import Path
from typing import DefaultDict
from typing import Iterable
import pandas as pd
from pydantic import BaseModel
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.file_util import FileUtil
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.storage.save_permanently_request import SavePermanentlyRequest
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED


def get_type_to_records_map(request: SavePermanentlyRequest) -> DefaultDict[type, TRecord]:
    """Fetch records from the database and return them."""

    request_type = TypeCache.get_class_from_type_name(request.type)
    type_hint = TypeHint.for_class(request_type, optional=True)

    key_objs = [_KEY_SERIALIZER.deserialize(key, type_hint) for key in request.keys]
    records = active(DataSource).load_many(key_objs)

    # TODO (Bohdan): Implement with_dependencies logic.
    # if request.with_dependencies:
    #     key_objs = [
    #         dag_node.data.node_data_reference
    #         for record in records.values()
    #         for dag_node in Dag.create_data_connection_dag_from_record(data=record).nodes
    #         if dag_node.data.node_data_reference
    #     ]
    #     records = active(DataSource).load_many(key_objs)

    type_to_records_map = defaultdict(list)
    for record in records:
        if record:
            type_to_records_map[type(record)].append(record)

    return type_to_records_map


class SavePermanentlyResponse(BaseModel):

    @classmethod
    def _get_extension(cls) -> str:
        """Return an extension in which records should be saved."""

        # TODO (Bohdan): Check if it makes sense to have a config which format/extension to use.
        #  If not - simplify the code.
        return "csv"

    @classmethod
    def _get_path_to_save_permanently_folder(cls) -> Path:
        """Return a path to a save permanently directory."""

        # TODO (Sasha): Provide a proper path to a save permanently folder instead of the current directory
        return Path()

    @classmethod
    def _write_records(cls, file_path: Path, records: Iterable[TRecord]) -> None:
        """Write serialized records on the disk."""

        file_extension = file_path.stem
        serialized_records = [DataSerializers.FOR_CSV.serialize(record) for record in records]

        if file_extension == "csv":
            df = pd.DataFrame([serialized_records])
            df.to_csv(file_path, mode="w", index=False, header=True)
        else:
            raise ValueError(f"File extension {file_extension} is not supported.")

    @classmethod
    def save_permanently(cls, request: SavePermanentlyRequest) -> "SavePermanentlyResponse":
        """Save records to the database on the disk."""

        for record_type, records in get_type_to_records_map(request).items():
            filename = f"{TypeUtil.name(record_type)}.{cls._get_extension()}"
            FileUtil.check_valid_filename(filename)
            file_path = cls._get_path_to_save_permanently_folder() / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            cls._write_records(file_path, records)

        return SavePermanentlyResponse()
