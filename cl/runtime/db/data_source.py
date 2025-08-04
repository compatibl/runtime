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
from typing import List

from cl.runtime.contexts.context_mixin import ContextMixin
from cl.runtime.db.data_source_key import DataSourceKey
from cl.runtime.db.dataset_key import DatasetKey
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.resource_key import ResourceKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class DataSource(DataSourceKey, RecordMixin, ContextMixin):
    """Rules for hierarchical lookup in multiple databases and datasets with data access control."""

    db: DbKey = required()
    """Database where lookup is performed (initialized to DB from the current context if not specified)."""

    dataset: DatasetKey = required()
    """Dataset within the database (initialized to the dataset from the current context if not specified)."""

    parents: List[DataSourceKey] | None = None
    """Search in parents in the specified order if the record is not found in self (optional)."""

    include: List[ResourceKey] | None = None
    """Unless the resource is in this list, continue to parents without searching in self (optional)."""

    exclude: List[ResourceKey] | None = None
    """If the resource is in this list, continue to parents without searching in self (optional)."""

    def get_key(self) -> DataSourceKey:
        return DataSourceKey(data_source_id=self.data_source_id).build()

    @classmethod
    def get_base_type(cls) -> type:
        return DataSource

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # If not specified, set based on the current context
        if self.db is None:
            pass  # TODO: Use current
        if self.dataset is None:
            pass  # TODO: Use current

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
            self.db = DataContext.load_one(self.db)  # TODO: Revise to use DB settings

        if self.db is not None:
            logger.info(f"Connected to Db of type '{TypeUtil.name(self.db)}', db_id = '{self.db.db_id}'.")