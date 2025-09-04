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
from typing import Any
from typing import cast
from inflection import titleize
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.services.screens import Screens
from cl.runtime.services.table_screen_item import TableScreenItem
from cl.runtime.services.type_screen_item import TypeScreenItem

# Create UI serializer
_UI_SERIALIZER = DataSerializers.FOR_UI


@dataclass(slots=True)
class DataService(DataclassMixin):
    """Service class for data-related actions."""

    @classmethod
    def run_screens(cls) -> dict[str, Any]:
        """Return data about screens that can be opened according to records in DB."""

        ds = active(DataSource)

        # Build 'tables' as a list of key types stored in db
        tables = [
            TableScreenItem(
                table_name=(key_type_name := typename(key_type)),
                label=titleize(key_type_name),
            )
            for key_type in ds.get_key_types()
        ]

        # Build 'types' as a list of record types stored in db
        types = [
            TypeScreenItem(
                type_name=(record_type_name := typename(record_type)),
                table_name=typename(TypeCache.from_type_name(record_type_name).get_key_type()),
                label=titleize(record_type_name),
            )
            for record_type in ds.get_record_types()
        ]

        # TODO (Roman): Implement 'filters' collection
        # Build 'filters' as a list of queries stored in db
        filters = []

        screens = Screens(
            tables=tables,
            types=types,
            filters=filters,
        )

        return cls._wrap_to_result(_UI_SERIALIZER.serialize(screens))

    @classmethod
    def run_select_table(cls, table_name: str):
        """Select records by table from DB."""

        # Get types stored in DB
        ds: DataSource = active(DataSource)

        # Select by table using load_all
        type_ = cast(type[KeyMixin], TypeCache.from_type_name(table_name))
        records = ds.load_all(type_)

        if records:
            common_base_record_type = ds.get_common_base_record_type(key_type=type_)
        else:
            common_base_record_type = type_

        # Get schema dict for type
        schema_dict = cls._get_schema_dict(common_base_record_type)

        result = {"Data": _UI_SERIALIZER.serialize(records), "Schema": schema_dict}
        return cls._wrap_to_result(result)

    @classmethod
    def run_select_type(cls, type_name: str):
        """Select records by type from DB."""

        # Get types stored in DB
        ds: DataSource = active(DataSource)

        # Select by type
        type_ = cast(type[RecordMixin], TypeCache.from_type_name(type_name))
        records = ds.load_by_type(type_)

        # Get schema dict for type
        schema_dict = cls._get_schema_dict(type_)

        result = {"Data": _UI_SERIALIZER.serialize(records), "Schema": schema_dict}
        return cls._wrap_to_result(result)

    @classmethod
    def run_select_filter(cls, table_name: str, filter_name: str):
        """Select records by filter from DB."""

        raise NotImplementedError("Select by filter currently is not supported.")

    @classmethod
    def _wrap_to_result(cls, result: Any) -> dict[str, Any]:
        # TODO (Roman): Temporary conversion according to the current UI format. Needs to be refactored
        return {"Result": result}

    @classmethod
    def _get_schema_dict(cls, type_: type | None) -> dict[str, dict]:
        """Create schema dict for type. If 'type_' is None - return empty dict."""
        return TypeResponseUtil.get_type(TypeRequest(type_name=type_.__name__)) if type_ is not None else dict()
