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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.typename import typename
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.views.empty_view import EmptyView
from cl.runtime.views.key_list_view import KeyListView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.record_list_view import RecordListView
from cl.runtime.views.record_view import RecordView
from cl.runtime.views.script import Script
from cl.runtime.views.script_language import ScriptLanguage
from cl.runtime.views.view import View

_LOGGER = logging.getLogger(__name__)

# Create serializers
_KEY_SERIALIZER = KeySerializers.DELIMITED
_UI_SERIALIZER = DataSerializers.FOR_UI


class PanelResponseUtil:
    """Response util for the /entity/panel route."""

    @classmethod
    def _get_content(cls, request: PanelRequest):
        """Implements /entity/panel route."""

        # Get the key type
        if TypeCache.is_known_type_name(request.type_name):
            # Static type is passed as type_name
            type_ = TypeCache.from_type_name(request.type_name)
            key_type = type_.get_key_type()
        else:
            # Table is passed as type_name
            key_type = active(DataSource).get_bound_key_type(table=request.type_name)

        # Deserialize key from string to object.
        key_obj = _KEY_SERIALIZER.deserialize(request.key, TypeHint.for_class(key_type))

        # Load record from the database.
        record = active(DataSource).load_one(key_obj)
        if record is None:
            raise RuntimeError(
                f"Record with type {request.type_name} and key {request.key} is not found in dataset {request.dataset}."
            )

        # Check if the selected type has the needed viewer and get its name (only viewer's label is provided).
        # Get handlers from TypeDecl.
        handlers = declare.handlers if (declare := TypeDecl.for_type(type(record)).declare) is not None else None

        if not handlers or not (
            viewer_name := next((h.name for h in handlers if h.label == request.panel_id and h.type_ == "Viewer"), None)
        ):
            raise RuntimeError(f"Type {typename(type(record))} has no view named '{request.panel_id}'.")

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
    def get_response(cls, request: PanelRequest):

        try:
            return cls._get_content(request)
        except Exception as e:
            # Log exception manually because the FastAPI logger will not be triggered.
            _LOGGER.error(str(e), exc_info=True)

            error_view = RecordView(
                view_for=request.key,
                view_name=request.panel_id,
                record=Script(  # noqa
                    name="Error message",
                    language=ScriptLanguage.MARKDOWN,
                    body=["## The following error occurred during the rendering of this view:\n", f"{str(e)}"],
                    word_wrap=True,
                ),
            )
            # Return custom error response.
            return cls._serialize_view(error_view)

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
        elif is_key(type(viewer_result)):
            return KeyView(view_for=view_for, view_name=view_name, key=viewer_result)

        # If the result is a Record, convert it to a RecordView.
        elif is_data_key_or_record(type(viewer_result)):
            return RecordView(view_for=view_for, view_name=view_name, record=viewer_result)

        # If the result is a list of keys or list of records, convert it to an appropriate View.
        elif isinstance(viewer_result, (list, tuple)):

            # Check iterable value type by first item.
            if is_key(type(viewer_result[0])):
                return KeyListView(view_for=view_for, view_name=view_name, keys=viewer_result)
            elif is_record(type(viewer_result[0])):
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
