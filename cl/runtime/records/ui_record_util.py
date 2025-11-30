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

import logging
from dataclasses import dataclass
from typing_extensions import Any
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_data_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_panel import RecordPanel
from cl.runtime.records.typename import typename
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.views.empty_view import EmptyView
from cl.runtime.views.key_list_view import KeyListView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.record_list_view import RecordListView
from cl.runtime.views.record_view import RecordView
from cl.runtime.views.script import Script
from cl.runtime.views.script_language import ScriptLanguage
from cl.runtime.views.view import View
from cl.runtime.views.view_persistence_util import ViewPersistenceUtil

_LOGGER = logging.getLogger(__name__)

# Create serializers
_KEY_SERIALIZER = KeySerializers.DELIMITED


@dataclass(slots=True, kw_only=True)
class UiRecordUtil(DataclassMixin):  # TODO: Move to the appropriate directory
    """
    Utility type to provide additional functionality for working with records.
    """

    @classmethod
    def run_get_record_panels(cls, type_name: str, key: str) -> list[RecordPanel]:
        """Get list of record's viewers with their types."""

        # TODO: Return saved view names
        request_type = TypeInfo.from_type_name(type_name)

        persisted_views = []

        # Get actual type from record if request.key is not None
        if key is not None:
            # Deserialize ui key
            key = _KEY_SERIALIZER.deserialize(key, TypeHint.for_type(request_type.get_key_type()))

            # If the record is not found, display panel tabs for the base type
            record = active(DataSource).load_one_or_none(key)
            actual_type = request_type if record is None else type(record)
            if record is not None:
                # Get persisted views for this record
                # TODO (Roman): Currently, loading Views by query does not work for Record types that have key fields
                #  of type 'date'. Fix query serialization so that it works for all supported types.
                try:
                    persisted_views = ViewPersistenceUtil.load_all_views_for_record(record)
                except Exception:
                    persisted_views = []
        else:
            actual_type = request_type

        # Get handlers from TypeDecl
        handlers = declare.handlers if (declare := TypeDecl.for_type(actual_type).declare) is not None else None

        result = [
            RecordPanel(name=pv.view_name, kind=ViewPersistenceUtil.get_panel_kind_from_view(pv), persistable=True)
            for pv in persisted_views
        ]

        if handlers:
            result += [
                RecordPanel(name=h.label, kind=cls._get_panel_kind(h), persistable=False)
                for h in handlers
                if h.type_ == "Viewer"
            ]

        return result

    @classmethod
    def run_load_record_panel(
        cls,
        type_name: str,
        key: str,
        panel_id: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Load the content of the record's viewer and return in dictionary format."""

        try:
            return cls._get_panel_content(type_name, key, panel_id, params)
        except Exception as e:
            # Log exception manually because the FastAPI logger will not be triggered.
            _LOGGER.error(str(e), exc_info=True)

            # Get the key type
            record_type = TypeInfo.from_type_name(type_name)
            key_type = record_type.get_key_type()

            # Deserialize key from string to object.
            key_obj = _KEY_SERIALIZER.deserialize(key, TypeHint.for_type(key_type))

            # Return custom error response
            error_view = Script(
                view_for=key_obj,
                view_name="Error message",
                language=ScriptLanguage.MARKDOWN,
                body=["## The following error occurred during the rendering of this view:\n", f"{str(e)}"],
                word_wrap=True,
            )
            return error_view

    @classmethod
    def _get_panel_kind(cls, handler: HandlerDeclareDecl) -> str | None:
        """Get type of the handler."""

        if handler.type_ == "Viewer" and handler.name == "self":
            return "Primary"
        else:
            return None

    @classmethod
    def _get_panel_content(
        cls,
        type_name: str,
        key: str,
        panel_id: str,
        params: dict[str, Any] | None = None,
    ):
        """Run viewer and process result."""

        # Get type of the record.
        type_ = TypeInfo.from_type_name(type_name)

        # Deserialize key from string to object.
        key_obj = _KEY_SERIALIZER.deserialize(key, TypeHint.for_type(type_.get_key_type()))

        # Load record from the database.
        record = active(DataSource).load_one(key_obj)
        if record is None:
            raise RuntimeError(f"Record with type {type_name} and key {key} is not found.")

        # Check if the selected type has the needed viewer and get its name (only viewer's label is provided).
        # Get handlers from TypeDecl.
        handlers = declare.handlers if (declare := TypeDecl.for_type(type(record)).declare) is not None else None
        # Try to get persisted view for this record and panel_id
        persisted_view = ViewPersistenceUtil.load_view_or_none(view_for=key_obj, view_name=panel_id)
        # Try to get dynamic viewer name
        viewer_name = next(
            (h.name for h in handlers if h.label == panel_id and h.type_ == "Viewer"),
            None,
        )

        if viewer_name is not None:
            # Use dynamic viewer method
            viewer = getattr(record, f"view_{viewer_name}")
            viewer_result = viewer()
            view = cls._process_viewer_result(viewer_result, view_for=record.get_key(), view_name=viewer_name)
        elif persisted_view is not None:
            # Use persisted view
            view = persisted_view
        else:
            raise RuntimeError(f"Type {typename(type(record))} has no view named '{panel_id}'.")

        # Load nested keys and perform custom View object transformations.
        view = view.materialize()

        return view

    @classmethod
    def _process_viewer_result(cls, viewer_result, view_for: KeyMixin, view_name: str) -> View:
        """
        Convert supported viewer result to the corresponding View object.

        The following viewer results are supported:
            - Record or list of records;
            - Key or list of keys;
            - Any View object;
            - None value.
        """

        # Handle empty result.
        if not viewer_result:
            return EmptyView(view_for=view_for, view_name=view_name)

        # If the result is a View object, fill in the missing key fields.
        elif isinstance(viewer_result, View):
            if viewer_result.view_for is None:
                viewer_result.view_for = view_for

            if viewer_result.view_name is None:
                viewer_result.view_name = view_name

            return viewer_result

        # If the result is a Key, convert it to a KeyView.
        elif is_key_type(type(viewer_result)):
            return KeyView(view_for=view_for, view_name=view_name, key=viewer_result)

        # If the result is a Record, convert it to a RecordView.
        elif is_data_key_or_record_type(type(viewer_result)):
            return RecordView(view_for=view_for, view_name=view_name, record=viewer_result)

        # If the result is a list of keys or list of records, convert it to an appropriate View.
        elif isinstance(viewer_result, (list, tuple)):
            # Check iterable value type by first item.
            first_item_type = type(viewer_result[0])  # TODO: Complete check instead of first item for viewer_result[0]
            if is_key_type(first_item_type):
                return KeyListView(view_for=view_for, view_name=view_name, keys=viewer_result)
            elif is_record_type(first_item_type) or is_data_type(first_item_type):
                return RecordListView(view_for=view_for, view_name=view_name, records=viewer_result)
            else:
                raise RuntimeError(
                    f"If the viewer result is iterable it must be a list of keys, list of records or list of data. "
                    f"Other is not supported. Received: {viewer_result}."
                )
        else:
            raise RuntimeError(f"Unsupported viewer result of type '{type(viewer_result)}': {viewer_result}.")
