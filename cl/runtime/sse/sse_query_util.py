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

from typing import Iterable
from cl.runtime import SqliteDb
from cl.runtime import TypeInfoCache
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.records.protocols import TRecord
from cl.runtime.serializers.data_serializers import DataSerializers

_SQLITE_SERIALIZER = DataSerializers.FOR_SQLITE


class SseQueryUtil:
    """
    Temporary util to perform query with simple conditions.
    TODO (Roman): Remove SseQueryUtil and use DbContext.query() instead when supported.
    """

    @classmethod
    def load_from_timestamp(
        cls,
        record_type: type[TRecord],
        *,
        from_timestamp: str | None = None,
        limit: int | None = None,
        timestamp_field_name: str = "timestamp",
    ) -> Iterable[TRecord]:
        """Load records of 'record_type' using timestamp and limit. Ordered by descending timestamp."""

        db_context = DbContext.current()
        db = db_context.db

        if isinstance(db, SqliteDb):
            return cls._load_from_timestamp_sqlite(
                db, record_type, from_timestamp=from_timestamp, limit=limit, timestamp_field_name=timestamp_field_name
            )
        else:
            raise RuntimeError(f"{cls.__name__} doesn't support current db type '{db.__class__.__name__}'.")

    @classmethod
    def _load_from_timestamp_sqlite(
        cls,
        db: SqliteDb,
        record_type: type[TRecord],
        *,
        from_timestamp: str | None,
        limit: int | None,
        timestamp_field_name: str,
    ) -> Iterable[TRecord]:
        """Load records of 'record_type' using timestamp and limit for Sqlite DB. Ordered by descending timestamp."""

        schema_manager = db._get_schema_manager()

        table_name: str = schema_manager.table_name_for_type(record_type)

        # If table doesn't exist return empty list
        if table_name not in schema_manager.existing_tables():
            return list()

        columns_mapping = schema_manager.get_columns_mapping(record_type.get_key_type())

        # Get subtypes for record_type and use them in match condition
        subtype_names = TypeInfoCache.get_child_names(record_type)
        query_values = [*subtype_names]
        value_placeholders = ", ".join(["?"] * len(subtype_names))
        sql_statement = f'SELECT * FROM "{table_name}" WHERE _type in ({value_placeholders})'

        # Add 'timestamp > from_timestamp' condition if present
        if from_timestamp is not None:
            sql_statement += f' AND "{columns_mapping[timestamp_field_name]}" > ?'
            query_values.append(from_timestamp)

        # Add order by 'timestamp'
        sql_statement += f' ORDER BY "{columns_mapping[timestamp_field_name]}" DESC'

        # Add limit condition if present
        if limit is not None:
            sql_statement += " LIMIT ?"
            query_values.append(limit)

        sql_statement += ";"

        reversed_columns_mapping = {v: k for k, v in columns_mapping.items()}

        cursor = db._get_connection().cursor()
        cursor.execute(sql_statement, query_values)

        for data in cursor.fetchall():
            data = {reversed_columns_mapping[k]: v for k, v in data.items() if v is not None}
            yield _SQLITE_SERIALIZER.deserialize(data)

        return None

    @classmethod
    def _load_from_timestamp_mongo(
        cls,
        db: BasicMongoDb,
        record_type: type[TRecord],
        *,
        from_timestamp: str | None,
        limit: int | None,
        timestamp_field_name: str,
    ) -> Iterable[TRecord] | None:
        raise NotImplementedError
