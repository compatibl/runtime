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
from typing import Any, Sequence

from cl.runtime.file.file_util import FileUtil
from cl.runtime.file.reader import Reader
from cl.runtime.primitive.char_util import CharUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.yaml_encoders import YamlEncoders

_SERIALIZER = DataSerializers.FOR_YAML_DESERIALIZATION
_ENCODER = YamlEncoders.DEFAULT


@dataclass(slots=True, kw_only=True)
class YamlReader(Reader):
    """Load records from YAML files into the context database."""

    def load_all(
        self,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> tuple[RecordMixin]:

        file_paths = FileUtil.enumerate_files(
            dirs=dirs,
            ext=ext,
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        # Iterate over files
        result = []
        for file_path in file_paths:
            try:
                record_type = FileUtil.get_type_from_filename(file_path, error=False)

                with open(file_path, mode="r", encoding="utf-8") as file:
                    yaml_data = _ENCODER.decode(file.read())

                    # Support both single record (dict) and multiple records (list)
                    if isinstance(yaml_data, dict):
                        object_dicts = [yaml_data]
                    elif isinstance(yaml_data, list):
                        object_dicts = yaml_data
                    else:
                        raise RuntimeError(
                            "YAML file must contain either a YAML object or an array of YAML objects."
                        )

                    invalid_objects = {
                        index
                        for index, object_dict in enumerate(object_dicts)
                        for key in object_dict.keys()
                        if key is None or key == ""
                    }

                    if invalid_objects:
                        rows_str = "".join([f"Row: {invalid_object}\n" for invalid_object in invalid_objects])
                        raise RuntimeError(
                            "Misaligned values found in the following objects.\n"
                            "Check the placement of colons, dashes and quotes.\n" + rows_str
                        )

                    # Deserialize rows into records and add to the result
                    loaded = [self._deserialize_object(record_type=record_type, object_dict=object_dict)
                              for object_dict in object_dicts]
                    result.extend(loaded)
            except Exception as e:
                raise RuntimeError(f"Failed to upload YAML file {file_path}.\n"
                                   f"Error: {e}") from e

        # Convert to tuple and return
        return tuple(result)

    @classmethod
    def _deserialize_object(cls, *, record_type: type | None, object_dict: dict[str, Any]) -> RecordMixin:
        """Deserialize YAML object into a record.
        Args:
            record_type: Record type hint derived from filename, or None if not available.
            object_dict: Dictionary representing the YAML object.
        Returns:
            Deserialized record.
        Raises:
            RuntimeError: If record type cannot be determined or deserialization fails.
         """

        # First, check if _type is provided in the YAML object
        # If _type is provided and valid, use it and ignore record_type from filename.
        if "_type" in object_dict:
            record_type_name = object_dict["_type"]

            # Get the actual record type from _type field
            try:
                record_type = TypeInfo.from_type_name(record_type_name)
            except Exception as e:
                # _type provided but invalid
                raise RuntimeError(
                    f"Could not determine record type '{record_type_name}'from YAML '_type'. Provide a valid type.\n"
                    f"Error: {e}"
                )

        # If record_type is still None, we cannot determine the type
        if record_type is None:
            raise RuntimeError(
                "Could not determine record type: "
                "YAML '_type' is missing/invalid and filename-derived type not available."
            )

        # Ensure _type is set for deserialization
        object_dict["_type"] = typename(record_type)

        result = _SERIALIZER.deserialize(object_dict).build()
        return result

