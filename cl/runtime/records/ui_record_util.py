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
from cl.runtime import RecordListView
from cl.runtime import RecordView
from cl.runtime import TypeCache
from cl.runtime import View
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.views.empty_view import EmptyView
from cl.runtime.views.key_list_view import KeyListView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.script import Script
from cl.runtime.views.script_language import ScriptLanguage

# Create serializers
_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


@dataclass(slots=True, kw_only=True)
class UiRecordUtil(DataMixin):
    """
    Utility type to provide additional functionality for working with records.
    """

    @classmethod
    def run_get_record_panels(cls, type_name: str, key: str) -> dict:
        """Get list of record's viewers with their types."""

        # TODO: Return saved view names
        request_type = TypeCache.get_class_from_type_name(type_name)

        # Get actual type from record if request.key is not None
        if key is not None:
            # Deserialize ui key
            key = _KEY_SERIALIZER.deserialize(key, TypeHint.for_class(request_type.get_key_type()))

            # If the record is not found, display panel tabs for the base type
            record = active(DataSource).load_one_or_none(key)
            actual_type = request_type if record is None else type(record)
        else:
            actual_type = request_type

        # Get handlers from TypeDecl
        handlers = declare.handlers if (declare := TypeDecl.for_type(actual_type).declare) is not None else None

        if handlers is not None and handlers:
            return {
                "Result": [
                    {"Name": handler.label, "Kind": cls._get_panel_kind(handler)}
                    for handler in handlers
                    if handler.type_ == "Viewer"
                ]
            }
        return {"Result": []}

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
            return {"Result": cls._get_panel_content(type_name, key, panel_id, params)}
        except Exception as e:
            # Log exception manually because the FastAPI logger will not be triggered.
            logger = logging.getLogger(__name__)
            logger.error(str(e), exc_info=True)

            error_view = RecordView(
                view_for=key,
                view_name=panel_id,
                record=Script(  # noqa
                    name="Error message",
                    language=ScriptLanguage.MARKDOWN,
                    body=["## The following error occurred during the rendering of this view:\n", f"{str(e)}"],
                    word_wrap=True,
                ),
            )
            # Return custom error response.
            return {"Result": cls._serialize_view(error_view)}

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
        type_ = TypeCache.get_class_from_type_name(type_name)

        # Deserialize key from string to object.
        key_obj = _KEY_SERIALIZER.deserialize(key, TypeHint.for_class(type_.get_key_type()))

        # Load record from the database.
        record = active(DataSource).load_one(key_obj)
        if record is None:
            raise RuntimeError(f"Record with type {type_name} and key {key} is not found.")

        # Check if the selected type has the needed viewer and get its name (only viewer's label is provided).
        # Get handlers from TypeDecl.
        handlers = declare.handlers if (declare := TypeDecl.for_type(type(record)).declare) is not None else None

        if not handlers or not (
            viewer_name := next((h.name for h in handlers if h.label == panel_id and h.type_ == "Viewer"), None)
        ):
            raise RuntimeError(f"Type {TypeUtil.name(record)} has no view named '{panel_id}'.")

        # Call viewer method and get the result.
        viewer = getattr(record, f"view_{viewer_name}")
        viewer_result = viewer()

        # Get View object for viewer result.
        view_for_key = _KEY_SERIALIZER.serialize(record.get_key())
        view = cls._process_viewer_result(viewer_result, view_for=view_for_key, view_name=viewer_name)

        # Load nested keys and perform custom View object transformations.
        view = view.materialize()

        # TODO (Roman): Remove custom serialization method when Generics is supported in base serialization.
        return cls._serialize_view(view)

    @classmethod
    def _process_viewer_result(cls, viewer_result, view_for: str, view_name: str) -> View:
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
        elif is_key(viewer_result):
            return KeyView(view_for=view_for, view_name=view_name, key=viewer_result)

        # If the result is a Record, convert it to a RecordView.
        elif is_data(viewer_result):
            return RecordView(view_for=view_for, view_name=view_name, record=viewer_result)

        # If the result is a list of keys or list of records, convert it to an appropriate View.
        elif isinstance(viewer_result, (list, tuple)):

            # Check iterable value type by first item.
            if is_key(viewer_result[0]):
                return KeyListView(view_for=view_for, view_name=view_name, keys=viewer_result)
            elif is_record(viewer_result[0]):
                return RecordListView(view_for=view_for, view_name=view_name, records=viewer_result)
            else:
                raise RuntimeError(
                    f"If the viewer result is iterable it must be a list of keys or a list of records. "
                    f"Other is not supported. Received: {viewer_result}."
                )
        else:
            raise RuntimeError(f"Unsupported viewer result of type '{type(viewer_result)}': {viewer_result}.")

    @classmethod
    def _serialize_view(cls, view: View):
        """
        Serialize View object with custom transformation for generic fields.
        Should be removed when supported Generics in base serialization.
        """

        if isinstance(view, RecordView):
            result = _UI_SERIALIZER.serialize(RecordView(view_for=view.view_for, view_name=view.view_name))
            result["Record"] = _UI_SERIALIZER.serialize(view.record)
            return result
        elif isinstance(view, RecordListView):
            result = _UI_SERIALIZER.serialize(RecordListView(view_for=view.view_for, view_name=view.view_name))
            result["Records"] = [_UI_SERIALIZER.serialize(record) for record in view.records if record is not None]
            return result
        else:
            return _UI_SERIALIZER.serialize(view)
