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

import importlib
import os
import sys
from dataclasses import dataclass
from importlib import import_module
from inspect import getmembers
from inspect import isclass
from pkgutil import walk_packages
from types import ModuleType
from typing import ClassVar
from typing import Collection
from typing import Self
from typing import Sequence
from memoization import cached
from more_itertools import consume
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.enum_util import EnumUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_data_type
from cl.runtime.records.protocols import is_enum_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_mixin_type
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.typename import qualname
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.project_settings import ProjectSettings

_TYPE_INFO_HEADERS = (
    "TypeName",
    "TypeKind",
    "QualName",
    "Subtype",
)
"""Headers of TypeInfo preload file."""


def is_schema_type(type_: type) -> bool:
    """Return true if the type should be included in schema, includes data types (except mixin types) and enums."""
    return isclass(type_) and (is_data_key_or_record_type(type_) or is_enum_type(type_))


@dataclass(slots=True, kw_only=True)
class TypeInfo(BootstrapMixin):
    """Information about a type stored in the type cache."""

    type_name: str
    """Unique type name (the same as class name except when alias is specified)."""

    type_kind: TypeKind
    """Type kind (primitive, enum, data, key, record)."""

    qual_name: str
    """Type qualname in module.ClassName format."""

    type_: type = required()
    """Class that corresponds to the type name or alias (populated in __init if not set on construction)."""

    subtype: str | None = None
    """Subtype for primitive types only (optional)."""

    _type_info_dict: ClassVar[dict[str, Self] | None] = None
    """Dictionary of TypeInfo indexed by type name."""

    _module_dict: ClassVar[dict[str, ModuleType] | None] = None
    """Dictionary of modules indexed by module name in dot-delimited format."""

    _packages: ClassVar[tuple[str, ...] | None] = None
    """List of packages to include in the cache."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.type_ is None:
            if self.qual_name is not None:
                self.type_ = self._import_type(qual_name=self.qual_name)
            else:
                raise RuntimeError("In TypeInfo class, qual_name field must be populated before build.")

    @classmethod
    @cached
    def is_known_type(cls, type_: type) -> bool:
        """Return True if a known data, key, or record type."""
        if isinstance(type_, type):
            return cls.is_known_type_name(typename(type_))
        else:
            raise RuntimeError(
                f"The argument of is_known_type is an instance of {type(type_).__name__} rather than type."
            )

    @classmethod
    @cached
    def is_known_type_name(cls, type_name: str) -> bool:
        """Return True if a known data, key, or record type name."""
        cls._ensure_loaded()

        if isinstance(type_name, str):
            # Return True if present in dict
            result = type_name in cls._type_info_dict
            return result
        else:
            raise RuntimeError(
                f"The argument of is_known_type_name is an instance of {type(type_name).__name__} rather than str."
            )

    @classmethod
    @cached
    def guard_known_type(
        cls,
        type_: type,
        *,
        type_kind: TypeKind | None = None,
        raise_on_fail: bool = True,
    ) -> bool:
        """
        Return True if the type is found in cache and matches type_kind  (if provided),
        otherwise return False or raise an error depending on raise_on_fail.

        Args:
            type_: Type to check
            type_kind: True only if matches the specified type kind if provided (optional)
            raise_on_fail: If the check fails, return False or raise an error depending on raise_on_fail.
        """
        return cls.guard_known_type_name(
            typename(type_),
            type_kind=type_kind,
            raise_on_fail=raise_on_fail,
        )

    @classmethod
    @cached
    def guard_known_type_name(
        cls,
        type_name: str,
        *,
        type_kind: TypeKind | None = None,
        raise_on_fail: bool = True,
    ) -> bool:
        """
        Return True if the type name is found in cache and matches type_kind  (if provided),
        otherwise return False or raise an error depending on raise_on_fail.

        Args:
            type_name: Type name in PascalCase format
            type_kind: True only if matches the specified type kind if provided (optional)
            raise_on_fail: If the check fails, return False or raise an error depending on raise_on_fail.
        """
        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        if type_kind is None:
            # If type_kind is None, only check if present in dict
            found = type_name in cls._type_info_dict
        else:
            # Otherwise get type_info
            type_info = cls._type_info_dict.get(type_name)
            if found := type_info is not None:
                # Type found in cache, compare type_kind
                if type_info.type_kind == type_kind:
                    return True
                elif raise_on_fail:
                    # Type kind mismatch, raise
                    raise RuntimeError(
                        f"Type {type_name} has type_kind={type_info.type_kind.name} "
                        f"while {type_kind.name} was expected."
                    )
                else:
                    # Type kind mismatch, return False
                    return False

        if found:
            # If found, type_kind was already checked
            return True
        elif raise_on_fail:
            # Not found and raise_on_fail is True, raise
            raise RuntimeError(f"Type name {type_name} is not found the environment's package list.")
        else:
            # Not found and raise_on_fail is False, return False
            return False

    @classmethod
    @cached
    def get_type_name_info(cls, type_name: str) -> Self:
        """Return type info if the type name is found in cache, error if not found."""
        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        result = cls._type_info_dict.get(type_name)
        if not result:
            packages_str = "\n".join(f"  - {package}" for package in cls._get_packages())
            raise RuntimeError(f"Type name {type_name} is not found in the imported package list:\n{packages_str}\n")

        # Invoking build imports the class and updates type_info.type_ in cache so it does not have to be imported again
        return result.build()

    @classmethod
    @cached
    def from_type_name(cls, type_name: str) -> type:
        """
        Get type from type name generated by typename(...) method, defaults to
        ClassName except when alias is defined to resolve a name collision.
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Next, try using cached qual name to avoid enumerating types in all packages
        if (type_info := cls._type_info_dict.get(type_name, None)) is not None:
            # Invoking build imports the class and updates type_info.type_ in cache so it does not have to be imported again
            return type_info.build().type_
        else:
            raise cls._type_name_not_found_error(type_name)

    @classmethod
    @cached
    def get_types(cls, *, type_kind: TypeKind | None = None) -> tuple[type, ...]:
        """
        Return already cached types, filter by TypeKind if specified.

        Args:
            type_kind: Restrict to the specified type kind if provided (optional)
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Filter by type_kind if specified
        type_info_objects = cls._type_info_dict.values()
        if type_kind is not None:
            type_info_objects = [type_info for type_info in type_info_objects if type_info.type_kind == type_kind]
        result = tuple(x.build().type_ for x in type_info_objects)
        return result

    @classmethod
    @cached
    def get_parent_and_self_type_names(cls, type_: type, *, type_kind: TypeKind | None = None) -> tuple[str, ...]:
        """
        Return a tuple of type names for parent types (inclusive of self) that match the predicate.

        Args:
            type_: Type for which the result is returned
            type_kind: Restrict to the specified type kind if provided (optional)
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get types
        result_types = cls.get_parent_and_self_types(type_, type_kind=type_kind)
        # Convert to names and sort
        return tuple(sorted(typename(x) for x in result_types))

    @classmethod
    @cached
    def get_parent_and_self_types(cls, type_: type, *, type_kind: TypeKind | None = None) -> tuple[type, ...]:
        """
        Return a tuple of parent types (inclusive of self) that match the predicate, sort by typename.

        Args:
            type_: Type for which the result is returned
            type_kind: Restrict to the specified type kind if provided (optional)
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get filtered list of MRO types
        result = cls._get_data_key_or_record_types(type_.mro(), type_kind=type_kind)
        return result

    @classmethod
    @cached
    def get_child_and_self_type_names(cls, type_: type, *, type_kind: TypeKind | None = None) -> tuple[str, ...]:
        """
        Return a tuple of type names for child types (inclusive of self) that match the predicate.
        Result is sorted by depth in hierarchy.

        Args:
            type_: Type for which the result is returned
            type_kind: Restrict to the specified type kind if provided (optional)
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get types
        result_types = cls.get_child_and_self_types(type_, type_kind=type_kind)
        # Convert to names and sort
        return tuple(sorted(typename(x) for x in result_types))

    @classmethod
    @cached
    def get_child_and_self_types(cls, type_: type, *, type_kind: TypeKind | None = None) -> tuple[type, ...]:
        """
        Return a tuple of type names for child types (inclusive of self) that match the predicate.
        Result is sorted by depth in hierarchy.

        Args:
            type_: Type for which the result is returned
            type_kind: Restrict to the specified type kind if provided (optional)
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Recursively load subtypes without filtering, because filter may apply to child but not parent
        subtypes_set = tuple(cls._get_unfiltered_child_types_set(type_))
        # Filter and sort
        result = cls._get_data_key_or_record_types(subtypes_set, type_kind=type_kind)
        return result

    @classmethod
    @cached
    def get_common_base_type(cls, types: Sequence[type]) -> type:
        """Return PascalCase record type name of the closest common base to the argument types."""

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Ensure the argument is not empty
        if not types:
            raise RuntimeError("The argument of get_common_base_type is None or empty.")

        # Dict where type is key and value is a set of its parents
        parent_dict = {x: set(TypeInfo.get_parent_and_self_types(x)) for x in types}
        # Set of all argument types and their parents, parents of parents are already included
        all_types = set(item for values in parent_dict.values() for item in values)
        # Dict where key is the number of parents and value is type
        all_types_depth_dict = {x: len(TypeInfo.get_parent_and_self_types(x)) for x in all_types}
        # Sort by the number of parents in descending order using negative length as sorting key
        sorted_all_types_depth_dict = dict(sorted(all_types_depth_dict.items(), key=lambda item: -item[1]))
        result = None
        for candidate_type in sorted_all_types_depth_dict.keys():
            is_common = all(candidate_type in parent_dict[other_type] for other_type in parent_dict)
            if is_common:
                # The dict is sorted in the reverse order of the number of parents,
                # break on the first common type which will have the most fields
                result = candidate_type
                break

        if result is not None:
            return result
        else:
            # Handle the case when common base is not found
            record_type_names_str = "\n".join(typename(x) for x in types)
            raise RuntimeError(f"No common base is found for the following records:\n{record_type_names_str}")

    @classmethod
    def rebuild(cls) -> None:
        """Reload types from packages and save a new TypeInfo.csv file to the bootstrap resources directory."""

        # Clear the existing data
        cls._clear()

        # Add each class after performing checks for duplicates
        consume(cls._add_class(class_) for class_ in cls._get_package_types())

        # Overwrite the cache file on disk with the new data
        cls._save()

    @classmethod
    def _get_packages(cls) -> tuple[str, ...]:
        """Get the list of packages specified in settings."""
        if cls._packages is None:
            # Get the list of packages from settings
            cls._packages = tuple(EnvSettings.instance().env_packages)
        return cls._packages

    @classmethod
    def _get_package_modules(cls) -> tuple[ModuleType, ...]:
        """Get the list of modules in the packages specified in settings."""
        modules = []
        packages = cls._get_packages()
        for package in packages:
            # Import root module of the package
            root_module = importlib.import_module(package)
            # Add the root module itself
            modules.append(root_module)
            # Get module info for all submodules, note the trailing period added per walk_packages documentation
            for module_info in walk_packages(root_module.__path__, root_module.__name__ + "."):
                module_name = module_info.name
                # Import the submodule using its full name
                submodule = importlib.import_module(module_name)
                modules.append(submodule)
        return tuple(sorted(modules, key=lambda x: x.__name__))

    @classmethod
    def _get_package_types(cls) -> tuple[type, ...]:
        """Get the list of types in the packages specified in settings."""
        # Enumerate types in all modules that match is_schema_type predicate
        modules = cls._get_package_modules()
        types = tuple(
            class_
            for module in modules
            for _, class_ in getmembers(module, is_schema_type)
            if module.__name__ == class_.__module__
        )
        return tuple(sorted(types, key=lambda x: x.__name__))

    @classmethod
    def _get_type_kind(cls, class_: type) -> TypeKind | None:
        """Get type kind of the class, return None if not a framework class."""
        if is_primitive_type(class_):
            return TypeKind.PRIMITIVE
        elif is_enum_type(class_):
            return TypeKind.ENUM
        elif is_key_type(class_):
            return TypeKind.KEY
        elif is_record_type(class_):
            return TypeKind.RECORD
        elif is_data_key_or_record_type(class_):
            return TypeKind.DATA
        else:
            # Return None if not a framework class
            return None

    @classmethod
    def _check_type(cls, type_: type) -> None:
        """Check that the class is in the package list."""

        # Error if the class is imported from a module that is not in the package list
        packages = cls._get_packages()
        if not any(type_.__module__.startswith(package) for package in packages):
            packages_str = "\n".join(f"  - {package}" for package in packages)
            raise RuntimeError(
                f"Buildable class {type_.__name__} is declared in module {type_.__module__}\n"
                f"which is not in one of the imported packages. Move the class to an imported package\n"
                f"so it can always be loaded from databases and storage, or exclude it via TypeExclude.csv.\n"
                f"Imported packages:\n{packages_str}"
            )

    @classmethod
    def _add_class(cls, class_: type, *, subtype: str | None = None) -> None:
        """Add the specified class to the qual_name and type_name dicts without overwriting the existing values."""

        # TODO: Exclude types in TypeExclude.csv

        # Error if the class is imported from a module that is not in the package list
        cls._check_type(class_)

        type_kind = cls._get_type_kind(class_)
        if type_kind is None:
            # Skip if not a framework class
            return

        if type_kind == TypeKind.PRIMITIVE:
            # Apply subtype if specified for a primitive type
            type_name = subtype if subtype else class_.__name__
        else:
            # Get type name with aliases applied
            type_name = typename(class_)
            # Ensure subtype is not specified for non-primitive types
            if subtype:
                raise RuntimeError(
                    f"Subtype {subtype} is specified for non-primitive class {class_.__name__}.\n"
                    f"Only primitive types can have subtypes."
                )

        # Get type info without subclass names (which will be done on second pass after all types are loaded)
        type_info = TypeInfo(
            type_name=type_name,
            type_kind=type_kind,
            qual_name=qualname(class_),
            type_=class_,
            subtype=subtype,
        ).build()

        # Populate the dictionary
        existing_info = cls._type_info_dict.setdefault(type_info.type_name, type_info)

        # In case of a name collision, the value of type field in existing_info will not match
        if existing_info.qual_name != type_info.qual_name:
            raise RuntimeError(
                f"Two types in the imported packages share the same type name: {type_info.type_name}\n"
                f"  - {existing_info.qual_name}\n"
                f"  - {type_info.qual_name}\n"
                f"Use TypeAlias.csv to resolve the name collision.\n"
            )

    @classmethod
    def _ensure_loaded(cls):
        """Load the data from TypeInfo.csv if not already loaded, do not reload."""

        if cls._type_info_dict is not None:
            # Already loaded, exit early
            return

        # Clear cache before loading
        cls._clear()

        # Read from the cache file
        # TODO: !!!!!!!! Move to CsvUtil
        cache_filename = cls._get_preload_filename()
        if os.path.exists(cache_filename):
            with open(cache_filename, "r") as file:
                rows = file.readlines()
        else:
            # Cache file does not exist, error message
            raise RuntimeError(f"TypeInfo file is not found at {cache_filename}\n, run init_type_info to create.")

        # Iterate over the rows of TypeInfo preload
        for row_index, row in enumerate(rows):

            # Remove leading and trailing whitespace from each comma-separated token
            row_tokens = tuple(x.strip() for x in row.split(","))

            if row_index == 0:
                # Check that the header row has expected values
                if row_tokens != _TYPE_INFO_HEADERS:
                    actual_headers_str = ", ".join(row_tokens)
                    expected_headers_str = ", ".join(_TYPE_INFO_HEADERS)
                    raise RuntimeError(
                        f"TypeInfo preload file has invalid headers.\n"
                        f"Preload file: {cache_filename}\n"
                        f"Actual headers: {actual_headers_str}\n"
                        f"Expected headers: {expected_headers_str}\n"
                    )
            else:
                # Parse a type info row
                if len(row_tokens) == len(_TYPE_INFO_HEADERS):
                    # Extract the type name and qual name from the tokens
                    type_name, type_kind, qual_name, subtype = row_tokens
                else:
                    expected_num_tokens = len(_TYPE_INFO_HEADERS)
                    actual_num_tokens = len(row_tokens)
                    raise RuntimeError(
                        f"Invalid number of comma-delimited tokens {actual_num_tokens} in TypeInfo, "
                        f"should be {expected_num_tokens}.\n"
                        f"Sample row: TypeName,TypeKind,module.ClassName,subtype\n"
                        f"Invalid row: {row.strip()}\n"
                    )

                # Create type info object without child class names
                # Invoking build imports the class and updates type_info.type_ in cache so it does not have to be imported again
                type_info = TypeInfo(
                    type_name=type_name,
                    type_kind=EnumUtil.from_str(TypeKind, type_kind),
                    qual_name=qual_name,
                    subtype=subtype,
                ).build()

                # Add to the type info dictionary
                existing_info = cls._type_info_dict.setdefault(type_info.type_name, type_info)

                # In case of a name collision, the value of type field in existing_info will not match
                if existing_info.qual_name != type_info.qual_name:
                    raise RuntimeError(
                        f"Two types in TypeInfo.csv share the same type name: {type_info.type_name}\n"
                        f"  - {existing_info.qual_name}\n"
                        f"  - {type_info.qual_name}\n"
                        f"Use TypeAlias.csv to resolve the name collision.\n"
                    )

    @classmethod
    def _save(cls) -> None:
        """Save qual name cache to disk (overwrites the existing file)."""
        # Tuples of (type_name, qual_name) sorted by type name
        cache_filename = cls._get_preload_filename()
        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w") as file:
            # Write header row
            file.write(",".join(_TYPE_INFO_HEADERS) + "\n")

            # Sort the TypeInfo dictionary by type name and iterate
            sorted_type_info_list = sorted(cls._type_info_dict.values(), key=lambda x: x.type_name)
            for type_info in sorted_type_info_list:

                # Format fields for writing
                type_name = type_info.type_name
                type_kind_str = EnumUtil.to_str(type_info.type_kind)
                qual_name = type_info.qual_name
                subtype = type_info.subtype

                # Write comma-separated values for each token, with semicolons-separated lists
                file.write(f"{type_name},{type_kind_str},{qual_name},{subtype}\n")

    @classmethod
    def _clear(cls) -> None:
        """Clear cache before loading or rebuilding."""
        cls._type_info_dict = {}
        cls._module_dict = {}

    @classmethod
    def _get_preload_filename(cls) -> str:
        """Get the filename for the qual name cache."""
        resources_root = ProjectSettings.get_resources_root()
        result = os.path.join(resources_root, "bootstrap/TypeInfo.csv")
        return result

    @classmethod
    def _get_type(cls, type_or_name: type | str) -> type:
        """Convert to type if provided as nas, passthrough if already a type."""
        if isinstance(type_or_name, str):
            # Convert to type if provided as name
            result = cls.from_type_name(type_or_name)
        elif isinstance(type_or_name, type):
            # Already a type
            result = type_or_name
        else:
            raise RuntimeError(
                f"An instance of {typename(type(type_or_name))} is passed where only str or type are accepted."
            )
        return result

    @classmethod
    def _get_data_key_or_record_types(cls, types_: Collection[type], *, type_kind: TypeKind | None) -> tuple[type, ...]:
        """
        Sort by type name and filter by type kind, or return data, key or record types if type kind is None,
        eliminate duplicates.

        Args:
            types_: Types to filter
            type_kind: Restrict to type kind if provided (optional), otherwise return data, key or record types
        """

        # Filter based on type_kind, only DATA, KEY, and RECORD are expected here
        if type_kind is None:
            predicate = is_data_key_or_record_type
        elif type_kind == TypeKind.DATA:
            predicate = is_data_type
        elif type_kind == TypeKind.KEY:
            predicate = is_key_type
        elif type_kind == TypeKind.RECORD:
            predicate = is_record_type
        else:
            raise ErrorUtil.enum_value_error(type_kind, TypeKind)

        # Eliminate the duplicates and filter by predicate, excluding any mixin types
        # because this method must follow single inheritance convention
        result = set(x for x in types_ if predicate(x) and not is_mixin_type(x))
        # Sort by type name and return
        result = tuple(sorted(result, key=lambda x: typename(x)))
        return result

    @classmethod
    @cached
    def _get_unfiltered_child_types_set(cls, type_: type) -> set[type]:  # TODO: Consider if self should be included
        """Return a tuple of child types (inclusive of self), may include duplicates."""

        # TODO: !! This must run after all types are loaded, refactor to ensure complete load,
        # TODO: consider filtering by parent instead of using subclasses
        subtypes = {type_} if is_data_key_or_record_type(type_) else set()  # Include self in subtypes
        for subtype in type_.__subclasses__():
            # Exclude self from subtypes
            if subtype is not type_:
                # Check that the subclass is in the package list
                cls._check_type(subtype)
                # Recurse into the subclass hierarchy, avoid adding duplicates
                subtypes.update(
                    x for x in cls._get_unfiltered_child_types_set(subtype) if is_data_key_or_record_type(x)
                )
        return subtypes

    @classmethod
    @cached
    def _import_type(cls, *, qual_name: str) -> type:
        """Import type using its fully qualified name in module.ClassName format."""

        # Split fully qualified name into dot-delimited snake_case module and PascalCase class name
        module_name, class_name = qual_name.rsplit(".", 1)

        # Load the module if not already in cache
        if (module := cls._module_dict.get(module_name, None)) is None:
            # Check that the module exists and is fully initialized
            module = sys.modules.get(module_name)
            module_spec = getattr(module, "__spec__", None) if module is not None else None
            module_initializing = getattr(module_spec, "_initializing", False) if module_spec is not None else None
            module_imported = module_initializing is False  # To ensure it is not another value evaluating to False

            # Import dynamically if not already imported, report error if not found
            if not module_imported:
                try:
                    # Use setdefault to avoid overwriting the module if
                    # it was added to the cache since the initial check
                    module = cls._module_dict.setdefault(module_name, import_module(module_name))
                except ModuleNotFoundError:
                    raise RuntimeError(f"Module {module_name} is not found in TypeInfo, run init_type_info to rebuild.")

        # Get class from module, report error if not found
        try:
            # Get class from module
            result = getattr(module, class_name)
            # Add to the qual_name and type_name dictionaries
            cls._add_class(result)
            return result
        except AttributeError:
            raise RuntimeError(f"Class {qual_name} is not found in TypeInfo, run init_type_info to rebuild.")

    @classmethod
    def _type_name_not_found_error(cls, type_name: str) -> RuntimeError:
        """Return error message for type name not found."""
        return RuntimeError(f"Type {type_name} is not found in TypeInfo, run init_type_info to rebuild.")
