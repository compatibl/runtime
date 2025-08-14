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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.records.protocols import TRecord, KeyProtocol
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.data_serializers import DataSerializers


class SseQueryUtil:
    """Temporary util to perform query with simple conditions."""

    @classmethod
    def query_sorted_desc_and_limited(cls, key_type: type[KeyProtocol], *, limit: int | None = None):
        """Query 'table' with sort by 'timestamp' in descending order and limit."""

        # TODO (Roman): Refactor to use active(DataSource). Needed features:
        #   - sort by specific field in descending order
        #   - limit sorted result

        table = TypeUtil.name(key_type)  # TODO: REFACTORING .removesuffix("Key")
        db = active(DataSource)._get_db()  # TODO: !!! Refactor to stop bypassing DataSource logic

        if isinstance(db, SqliteDb):
            return cls._query_sorted_desc_and_limited_sqlite(
                db,
                table,
                sort_by_desc="timestamp",
                limit=limit,
            )
        elif isinstance(db, BasicMongoDb):
            return cls._query_sorted_mongo(
                db,
                table,
                sort_by_desc="timestamp",
                limit=limit,
            )
        else:
            raise RuntimeError(f"{cls.__name__} doesn't support current db type '{db.__class__.__name__}'.")

    @classmethod
    def _query_sorted_desc_and_limited_sqlite(
        cls,
        db: SqliteDb,
        table: str,
        *,
        sort_by_desc: str,
        limit: int | None,
    ) -> Iterable[TRecord]:

        if not db._is_table_exists(table):
            return tuple()

        select_sql, values = f"SELECT * FROM {db._quote_identifier(table)}", []

        # Add order by '_key' condition
        select_sql += f" ORDER BY {db._quote_identifier(sort_by_desc)} DESC"

        # Add 'limit' condition
        select_sql, add_params = db._add_limit_and_skip(select_sql, limit=limit)
        values.extend(add_params)

        # Execute SQL query
        conn = db._get_connection()
        cursor = conn.execute(select_sql, values)

        # Deserialize records
        result = []
        for row in cursor.fetchall():
            # Convert sqlite3.Row to dict
            serialized_record = {k: row[k] for k in row.keys() if row[k] is not None}
            del serialized_record["_key"]

            # Create a record from the serialized data
            record = DataSerializers.FOR_SQLITE.deserialize(serialized_record)

            result.append(record)

        return tuple(result)

    @classmethod
    def _query_sorted_mongo(
        cls,
        db: BasicMongoDb,
        table: str,
        *,
        sort_by_desc: str,
        limit: int | None,
    ) -> Iterable[TRecord]:

        # Get collection
        collection = db._get_mongo_collection(table)

        # Get iterable from the query, execution is deferred
        serialized_records = collection.find().sort(sort_by_desc, direction=-1)

        # Apply skip and limit to the iterable
        serialized_records = db._apply_limit_and_skip(serialized_records, limit=limit)

        result = tuple(
            DataSerializers.FOR_MONGO.deserialize(
                {k: v for k, v in serialized_record.items() if k not in {"_id", "_key"}}
            )
            for serialized_record in serialized_records
        )
        return result
