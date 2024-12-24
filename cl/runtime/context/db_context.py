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
from typing import Iterable
from typing import Type
from typing_extensions import Self
from cl.runtime import Db, Context, ClassInfo
from cl.runtime.context.base_context import BaseContext
from cl.runtime.context.env_util import EnvUtil
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.protocols import TKey
from cl.runtime.db.protocols import TRecord
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_key
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class DbContext(BaseContext):
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
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Db"

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        # Do not execute this code on frozen or deserialized context instances
        #   - If the instance is frozen, init_all has already been executed
        #   - If the instance is deserialized, init_all has been executed before serialization
        if not self.is_deserialized:

            # Get context settings
            context_settings = ContextSettings.instance()

            # Use database class from settings if not specified directly
            if self.db is None:
                if (current_context := DbContext.current_or_none()) is not None:
                    # Use DB from the current DbContext at the time of init execution
                    self.db = current_context.db
                else:
                    # Otherwise use default DB
                    self.db = self._get_default_db()

            # Use root dataset if not specified directly
            if self.dataset is None:
                self.dataset = DatasetUtil.root()

            #  Load 'db' field of this context using 'Context.current()'
            if self.db is not None and is_key(self.db):
                self.db = DbContext.load_one(DbKey, self.db)  # TODO: Revise to use DB settings

        # Return self to enable method chaining
        return self

    def __enter__(self):
        """Supports 'with' operator for resource disposal."""

        # Call '__enter__' method of base first
        Context.__enter__(self)

        try:
            # Execute on default (root) context instances only if they are not deserialized
            # (e.g. not the instances passed to a task queue)
            if self.db is not None and not self.is_deserialized:
                # Delete all existing data in temp database and drop DB in case it was not cleaned up
                # due to abnormal termination of the previous test run
                self.db.delete_all_and_drop_db()  # noqa
        except Exception as e:
            # Treat the exception as though it happened outside the 'with' clause:
            #   - Call __exit__ method of base class without passing exception details
            #   - Then rethrow the exception
            Context.__exit__(self, None, None, None)
            raise e

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Supports 'with' operator for resource disposal."""

        try:
            # Execute on default (root) context instances only if they are not deserialized
            # (e.g. not the instances passed to a task queue)
            if self.db is not None and not self.is_deserialized:
                # Delete all data in temp database and drop DB to clean up
                self.db.delete_all_and_drop_db()  # noqa
        except Exception as e:
            # Treat the exception as though it happened outside the 'with' clause:
            #   - Call __exit__ method of base class without passing exception details
            #   - Then rethrow the exception
            Context.__exit__(self, None, None, None)
            raise e
        else:
            # Otherwise delegate to the __exit__ method of base
            return Context.__exit__(self, exc_type, exc_val, exc_tb)
    
    @classmethod
    def get_db(cls) -> Db:
        """
        Return DB for the current DbContext inside the 'with DbContext(...)' clause.
        Return the default DB from settings outside the outermost 'with DbContext(...)' clause.
        """
        if (db_context := DbContext.current_or_none()) is not None:
            # Use DB from the current context
            return db_context.db
        else:
            # Use default DB
            return cls._get_default_db()

    @classmethod
    def get_dataset(cls) -> str | None:
        """
        Unique dataset in backslash-delimited format obtained by concatenating identifiers from the DbContext stack
        for the same DB as the current context in the order entered, or None outside 'with DbContext(...)' clause.

        Notes:
          - If dataset field is None for any dataset in the stack, it is is disregarded
          - If dataset field is None for the entire the DbContext stack, this method returns root dataset
        """
        if (current_context := DbContext.current_or_none()) is not None:
            # Gather those tokens that are not None from contexts that have the same DB as the current context
            current_db_id = current_context.db.db_id
            tokens = [
                dataset for context in cls._get_context_stack() 
                if current_db_id == context.db.db_id and (dataset := context.dataset) is not None
            ]
            # Consider the possibility that after removing tokens that are None, the list becomes empty
            if tokens:
                # Concatenate datasets from the context stack for the same DB as the current context
                return "\\".join(tokens)
            else:
                # Return root dataset if empty
                return DatasetUtil.root()
        else:
            # Return root dataset outside the outermost 'with DbContext(...)' clause
            return DatasetUtil.root()

    @classmethod
    def load_one(
        cls,
        record_type: Type[TRecord],
        record_or_key: TRecord | KeyProtocol | None,
        *,
        dataset: str | None = None,
        identity: str | None = None,
        is_key_optional: bool = False,
        is_record_optional: bool = False,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup)

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            record_or_key: Record (returned without lookup) or key in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            identity: Identity token for database access and row-level security
            is_key_optional: If True, return None when key is none found instead of an error
            is_record_optional: If True, return None when record is not found instead of an error
        """
        return cls.get_db().load_one(  # noqa
            record_type,
            record_or_key,
            dataset=dataset,
            identity=identity,
            is_key_optional=is_key_optional,
            is_record_optional=is_record_optional,
        )

    @classmethod
    def load_many(
        cls,
        record_type: Type[TRecord],
        records_or_keys: Iterable[TRecord | KeyProtocol | tuple | str | None] | None,
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            identity: Identity token for database access and row-level security
        """
        return cls.get_db().load_many(  # noqa
            record_type,
            records_or_keys,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def load_all(
        cls,
        record_type: Type[TRecord],
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load all records of the specified type and its subtypes (excludes other types in the same DB table).

        Args:
            record_type: Type of the records to load
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            identity: Identity token for database access and row-level security
        """
        return cls.get_db().load_all(  # noqa
            record_type,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def load_filter(
        cls,
        record_type: Type[TRecord],
        filter_obj: TRecord,
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> Iterable[TRecord]:
        """
        Load records where values of those fields that are set in the filter match the filter.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            filter_obj: Instance of 'record_type' whose fields are used for the query
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            identity: Identity token for database access and row-level security
        """
        return cls.get_db().load_filter(  # noqa
            record_type,
            filter_obj,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def save_one(
        cls,
        record: RecordProtocol | None,
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            record: Record or None.
            dataset: Target dataset as a delimited string, list of levels, or None
            identity: Identity token for database access and row-level security
        """
        cls.get_db().save_one(  # noqa
            record,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def save_many(
        cls,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            records: Iterable of records.
            dataset: Target dataset as a delimited string, list of levels, or None
            identity: Identity token for database access and row-level security
        """
        cls.get_db().save_many(  # noqa
            records,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def delete_one(
        cls,
        key_type: Type[TKey],
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> None:
        """
        Delete one record for the specified key type using its key in one of several possible formats.

        Args:
            key_type: Key type to delete, used to determine the database table
            key: Key in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            identity: Identity token for database access and row-level security
        """
        cls.get_db().delete_one(  # noqa
            key_type,
            key,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def delete_many(
        cls,
        keys: Iterable[KeyProtocol] | None,
        *,
        dataset: str | None = None,
        identity: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

        Args:
            keys: Iterable of keys.
            dataset: Target dataset as a delimited string, list of levels, or None
            identity: Identity token for database access and row-level security
        """
        cls.get_db().delete_many(  # noqa
            keys,
            dataset=dataset,
            identity=identity,
        )

    @classmethod
    def _get_default_db(cls):
        """Get default DB from settings."""
        # Get context settings
        context_settings = ContextSettings.instance()

        # Create the database class specified in settings
        db_type = ClassInfo.get_class_type(context_settings.db_class)

        # If not inside a test
        if not Settings.is_inside_test:

            # Use db_id from settings for context_id unless specified by the caller
            if context_settings.context_id is not None:
                db_id = context_settings.context_id
            else:
                db_id = Settings.process_timestamp

        # Inside test
        else:

            # For a test, env name is dot-delimited test module, class in snake_case (if any), and method or function
            env_name = EnvUtil.get_env_name()

            # Use 'temp' followed by context_id converted to semicolon-delimited format for db_id
            db_id = "temp;" + env_name.replace(".", ";")

        # Create and return
        result = db_type(db_id=db_id)
        return result
