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

from dataclasses import dataclass
from logging import getLogger
from typing import Iterable
from typing import Sequence
from cl.runtime import Db
from cl.runtime.contexts.context_mixin import ContextMixin
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_singleton_key
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in cache lookup."""


@dataclass(slots=True, kw_only=True)
class DbContext(ContextMixin):
    """Includes database and dataset."""

    db: Db | None = None
    """Database of the storage context."""

    dataset: str | None = None
    """
    Dataset can be a single token or multiple tokens in backslash-delimited format.

    Notes:
      - Datasets for the DbContext stack are concatenated in the order entered separately for each DB
      - Because 'with' clause cannot be under if/else, in some cases dataset may be None
        but 'with DbContext(...)' clause would still be present.
      - If dataset is None, it is is disregarded
      - If dataset is None for the entire the DbContext stack, this method returns None
    """

    @classmethod
    def get_base_type(cls) -> type:
        return DbContext

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        logger = getLogger(__name__)

        # Initialize from the current context
        if self.db is None:
            self.db = self._get_db()

        # TODO: !!! Currently, only the latest context is reproduced in celery workers
        #       This may cause problems with the current design and has to be reviewed
        # Get previous dataset value from the latest context in context stack that has the same DB
        reversed_stack = reversed(self.get_context_stack())
        # Set to root dataset if no previous contexts with the same DB are found in context stack
        previous_dataset = next(
            (context.dataset for context in reversed_stack if context.db.db_id == self.db.db_id), DatasetUtil.root()
        )

        if self.dataset:
            # If specified for this instance, combine with previous using backslash separator
            self.dataset = f"{previous_dataset}\\{self.dataset}"
        else:
            # Otherwise use previous
            self.dataset = previous_dataset

        #  Load 'db' field of this context using 'Context.current()'
        if self.db is not None and is_key(self.db):
            self.db = DbContext.load_one(self.db)  # TODO: Revise to use DB settings

        if self.db is not None:
            logger.info(f"Connected to Db of type '{TypeUtil.name(self.db)}', db_id = '{self.db.db_id}'.")

    @classmethod
    def get_db_id(cls) -> str:
        """Get db_id of the database from the current context or error message if not inside 'with DbContext(...)' clause."""
        return cls._get_db().db_id

    @classmethod
    def get_dataset(cls, dataset: str | None = None) -> str | None:
        """
        Unique dataset in backslash-delimited format obtained by concatenating identifiers from the DbContext stack
        for the same DB as the current context in the order entered, or None outside 'with DbContext(...)' clause.
        The result is combined with dataset. If the overall result is None, root dataset is used.
        """
        if (context := cls.current_or_none()) is not None:
            # Use the value from the current context if not None
            return context.dataset
        else:
            # Otherwise return root dataset
            return DatasetUtil.root()

    @classmethod
    def get_bindings(cls) -> tuple[TableBinding, ...]:
        """
        Return table to record type bindings in alphabetical order of table name followed by record type name.

        Notes:
            More than one table can exist for the same record type and vice versa.
        """
        return cls._get_db().get_bindings()

    @classmethod
    def get_tables(cls) -> tuple[str, ...]:
        """Return DB table names in alphabetical order of non-delimited PascalCase format."""
        return cls._get_db().get_tables()

    def get_record_type_names(cls) -> tuple[str, ...]:
        """
        Return non-delimited PascalCase record type names in alphabetical order for records stored in this DB.

        Notes:
            More than one table can exist for the same record type.
        """
        return cls._get_db().get_record_type_names()

    @classmethod
    def get_bound_tables(cls, *, record_type: type[RecordProtocol] | str) -> tuple[str, ...]:
        """
        Return tables for the specified record type or name in alphabetical order.

        Returns:
            Table names in non-delimited PascalCase format.

        Args:
            record_type: Record type or name for which the tables are returned.
        """
        return cls._get_db().get_bound_tables(record_type=record_type)

    @classmethod
    def get_bound_key_type(cls, *, table: str) -> type:
        """
        Key type for the specified table, table must exist.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        return cls._get_db().get_bound_key_type(table=table)

    @classmethod
    def get_bound_record_type_names(cls, *, table: str) -> tuple[str, ...]:
        """
        Return non-delimited PascalCase record type names in alphabetical order stored in the specified table.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        return cls._get_db().get_bound_record_type_names(table=table)

    @classmethod
    def get_allowed_record_type_names(cls, *, table: str) -> tuple[str, ...]:
        """
        Record type names that may be stored in the specified table, table must exist.

        Returns:
            Tuple of non-delimited PascalCase record type names in alphabetical order.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        return cls._get_db().get_allowed_record_type_names(table=table)

    @classmethod
    def get_lowest_bound_record_type_name(cls, *, table: str) -> str:
        """
        Return the name of the lowest common type for the record types bound to the table, error if the table is empty.

        Returns:
            Non-delimited PascalCase record type name.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        return cls._get_db().get_lowest_bound_record_type_name(table=table)

    @classmethod
    def load_one(
        cls,
        record_or_key: TKey,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return cls._get_db().load_one(
            record_or_key,
            dataset=dataset,
            cast_to=cast_to,
        )

    @classmethod
    def load_one_or_none(
        cls,
        record_or_key: TKey | None,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return cls._get_db().load_one_or_none(
            record_or_key,
            dataset=dataset,
            cast_to=cast_to,
        )

    @classmethod
    def load_many(
        cls,
        records_or_keys: Sequence[TRecord | TKey | None] | None,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return cls._get_db().load_many(
            records_or_keys,
            dataset=dataset,
            cast_to=cast_to,
        )

    @classmethod
    def load_type(
        cls,
        filter_to: type[TRecord],
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord]:
        """
        Load all records of 'filter_to' type and its subtypes from all tables where they are stored.

        Args:
            filter_to: The query will return only this type and its subtypes
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return cls._get_db().load_type(
            filter_to,
            dataset=dataset,
            cast_to=cast_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    @classmethod
    def load_table(
        cls,
        table: str,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord]:
        """
        Load all records from the specified table.

        Args:
            table: The table from which the records are loaded
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        result = cls._get_db().load_table(
            table,
            dataset=cls.get_dataset(dataset),
            cast_to=cast_to,
            filter_to=filter_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )
        return result

    @classmethod
    def load_where(
        cls,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        result = cls._get_db().load_where(
            query,
            dataset=cls.get_dataset(dataset),
            cast_to=cast_to,
            filter_to=filter_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )
        return result

    @classmethod
    def count_where(
        cls,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        filter_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query using the current context's DB.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            filter_to: Count only the subtypes of this type (defaults to the query target type)
        """
        db = cls._get_db()
        return db.count_where(query, dataset=dataset, filter_to=filter_to)

    @classmethod
    def save_one(
        cls,
        record: RecordProtocol,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            record: Record or None.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        # TODO (Roman): Consider removing it because we also perform checks in the Db class.
        # Perform pre-save check
        cls._pre_save_check(record)

        # Invoke DB method with combined dataset
        cls._get_db().save_many(  # noqa
            [record],
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def save_many(
        cls,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            records: Iterable of records.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        # Convert to list, this must be done first to ensure single traversal of generator
        # TODO: Do this incrementally for a large number of records
        records = list(records)

        # TODO (Roman): Consider removing it because we also perform checks in the Db class.
        # Perform pre-save check for each record
        [cls._pre_save_check(record) for record in records]

        # Invoke save_many method of DB implementation
        cls._get_db().save_many(  # noqa
            records,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def delete_one(
        cls,
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete one record for the specified key type using its key in one of several possible formats.

        Args:
            key: Key in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls.delete_many([key], dataset=dataset)

    @classmethod
    def delete_many(
        cls,
        keys: Sequence[TKey | None] | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

        Args:
            keys: Sequence of keys to delete.
            dataset: Target dataset as a delimited string, list of levels, or None
        """
        return cls._get_db().delete_many(
            keys,
            dataset=dataset,
        )

    @classmethod
    def drop_test_db(cls) -> None:
        """
        Drop a database as part of a unit test.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - The method is invoked from a unit test based on ProcessContext.is_testing()
        - db_id starts with db_test_prefix specified in settings.yaml (the default prefix is 'test_')
        """
        cls._get_db().drop_test_db()

    @classmethod
    def drop_temp_db(cls, *, user_approval: bool) -> None:
        """
        Drop a temporary database with explicit user approval.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - user_approval is true
        - db_id starts with db_temp_prefix specified in settings.yaml (the default prefix is 'temp_')
        """
        cls._get_db().drop_temp_db(user_approval=user_approval)

    @classmethod
    def _get_db(cls) -> Db:
        """
        Return DB for the current DbContext inside the 'with DbContext(...)' clause.
        Return the default DB from settings outside the outermost 'with DbContext(...)' clause.
        """
        if (db_context := DbContext.current_or_none()) is not None:
            # Use the value from the current context if not None
            return db_context.db
        else:
            if ProcessContext.is_testing():
                raise RuntimeError(
                    "To use DB in a test, specify default_db_fixture or similar pytest fixture or "
                    "use 'with DbContext(...)' clause if not using pytest."
                )
            else:
                raise RuntimeError("Attempting to access DB outside the outermost 'with DbContext(...)' clause.")

    @classmethod
    def _pre_save_check(cls, record: RecordProtocol) -> None:
        if record is None:
            # Confirm argument is not None
            raise RuntimeError("Record passed to DB save method is None.")
        elif not is_record(record):
            # Confirm the argument is a record
            raise RuntimeError(f"Attempting to an object of {type(record).__name__} which is not a record.")
        elif not record.is_frozen():
            raise RuntimeError(
                f"Build method not invoked before saving for an record of type\n"
                f"{TypeUtil.name(record)} with key {record.get_key()}\n"
            )
        else:
            # TODO: To prevent calling get_key more than once, pass to DB save method
            if not KeySerializers.DELIMITED.serialize(key := record.get_key()):
                # Error only if not a singleton
                if not is_singleton_key(key):
                    record_data_str = BootstrapSerializers.YAML.serialize(record)
                    raise RuntimeError(
                        f"Attempting to save a record with empty key, invoke build before saving.\n"
                        f"Values of other fields:\n{record_data_str}"
                    )
