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

from types import UnionType
from typing import Dict
from typing import List
from typing import Type
from typing import Union

class_hierarchy_annotations_dict: Dict[Type, Dict[str, Type]] = dict()
"""Dictionary of class hierarchy annotations."""


class AnnotationsUtil:
    """Util class for type annotations."""

    @classmethod
    def get_class_hierarchy_annotations(cls, data_type) -> Dict[str, Type]:
        """
        Return combined annotations dict for all classes in data_type hierarchy.
        Checks type of fields with the same name and raises RuntimeError if there is a conflict.
        """
        if (result := class_hierarchy_annotations_dict.get(data_type, None)) is not None:
            # Use cached value
            return result
        else:
            # Collect all annotations in hierarchy

            # Combined annotations for all types in hierarchy {field_name: field_type}
            hierarchy_annots: Dict[str, Type] = {}

            for base in reversed(data_type.__mro__):
                if annot := getattr(base, "__annotations__", None):
                    for name_, type_ in annot.items():
                        # TODO (Roman): Implement function to check type conflicts
                        #   Resolve if type in annotations is string
                        hierarchy_annots[name_] = type_

            return hierarchy_annots

    @classmethod
    def handle_optional_annot(cls, type_):
        """Extract inner type if 'type_' is Optional[...], otherwise return unchanged."""

        if type_ is None:
            return None

        # Check if type_ is a UnionType or Union and process if only one argument is not None.
        if (type_.__class__ is UnionType or getattr(type_, "__origin__", None) is Union) and (
            union_args := getattr(type_, "__args__", None)
        ):
            not_none_union_args: List[int] = [arg for arg in union_args if arg is not type(None)]
            if len(not_none_union_args) == 1:
                return not_none_union_args[0]
            else:
                raise RuntimeError(f"Can not process Union: {type_}.")

        # Return type_ if it is not Union
        return type_

    @classmethod
    def extract_list_value_annot_type(cls, type_):
        """Extract generic type arguments from list annotation type, e.g. List[int] -> int"""

        if type_ is None or (type_args := getattr(type_, "__args__", None)) is None:
            return None
        else:
            if len(type_args) == 1:
                # Take first argument as value type
                return type_args[0]
            else:
                raise RuntimeError(f"Can not extract list value annotation type from '{type_}'.")

    @classmethod
    def extract_tuple_value_annot_type(cls, type_):
        """Extract generic type arguments from tuple annotation type, e.g. Tuple[int, ...] -> int"""

        if type_ is None or (type_args := getattr(type_, "__args__", None)) is None:
            return None
        else:
            if len(type_args) == 2:
                # The second type argument is expected to be an ellipsis.
                if type_args[1] is not ...:
                    raise RuntimeError(f"Tuple type annotation format should be Tuple[Type, ...]. Received: {type_}.")

                # Take first argument as value type
                return type_args[0]
            else:
                raise RuntimeError(f"Can not extract tuple value annotation type from '{type_}'.")

    @classmethod
    def extract_dict_value_annot_type(cls, type_):
        """Extract generic type arguments from dict annotation type, e.g. Dict[str, int] -> int"""

        if type_ is None or (type_args := getattr(type_, "__args__", None)) is None:
            return None
        else:
            if len(type_args) == 2:
                # Take second argument as value type
                return type_args[1]
            else:
                raise RuntimeError(f"Can not extract dict value annotation type from '{type_}'.")
