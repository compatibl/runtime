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

from abc import ABC
from dataclasses import MISSING
from dataclasses import dataclass
from typing import ClassVar
from typing import Self
from typing import Sequence
from dotenv import find_dotenv
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.settings.dynaconf_loader import ENVVAR_PREFIX
from cl.runtime.settings.dynaconf_loader import DynaconfLoader

PROCESS_TIMESTAMP = Timestamp.create()
"""Unique UUIDv7-based timestamp set during the Python process launch."""


@dataclass(slots=True, kw_only=True)
class Settings(BootstrapMixin, ABC):
    """
    Abstract base of settings classes.

    Notes:
      - Fields in a settings class SampleSettings must begin from settings_
      - Dynaconf fields in YAML files for SampleSettings match SampleSettings field names including settings_ prefix
      - Environment variable name is the global prefix (CL_ by default) followed by UPPER_CASE settings field name
        for example 'CL_SAMPLE_FIELD' for the field 'sample_field' in SampleSettings
      - Environment variables will override the matching field in YAML files across all settings directories.
    """

    __settings_dict: ClassVar[dict[tuple[str | None, type], Self]] = {}
    """Dictionary of Settings instances indexed by the relative settings dir and final class type."""

    @classmethod
    def get_prefix(cls) -> str:
        """
        Dynaconf fields will be filtered by 'prefix_' before being passed to the settings class constructor.
        Defaults to the class name converted to snake_case with 'Settings' suffix removed.

        Notes:
            - If this method provides an override of the default prefix, the returned prefix must be lowercase
            - and must not start or end with underscore (but may include underscore separators)
        """
        result = CaseUtil.pascal_to_snake_case(typename(cls)).removesuffix("_settings")
        result = result if result.endswith("_") else f"{result}_"
        return result

    @classmethod
    def instance(cls, *, package: str | None = None) -> Self:
        """
        Singleton instance of Self with only those fields that match the prefix returned Self.get_prefix().
        If package is specified, {package_dir}/{package_namespace}.yaml is added to settings with lower
        priority than the primary settings files.

        Args:
            package: Package namespace, e.g. 'cl.runtime' (optional)
        """

        # Check for an existing settings object, return if found, otherwise continue
        settings_dict_key = (package, cls)
        if (result := cls.__settings_dict.get(settings_dict_key, None)) is not None:
            return result

        # Get DynaconfLoader instance for the specified package
        loader = DynaconfLoader.instance(package=package)

        # Get and validate the field prefix to filter Dynaconf fields for this settings class
        prefix = cls.get_prefix()
        prefix_description = f"Dynaconf settings prefix '{prefix}' for {typename(cls)}"
        if prefix is None:
            raise RuntimeError(f"{prefix_description} is None.")
        if prefix == "":
            raise RuntimeError(f"{prefix_description} is an empty string.")
        if not prefix.islower():
            raise RuntimeError(f"{prefix_description} must be lowercase.")
        if prefix.startswith("_"):
            raise RuntimeError(f"{prefix_description} must not start with an underscore.")
        if not prefix.endswith("_"):
            raise RuntimeError(f"{prefix_description} must end with an underscore.")

        # Exclude fields without prefix from the base Settings class
        excluded_fields = ["settings_dir"]
        class_fields = [slot for slot in cls.get_field_names() if slot not in excluded_fields]

        # Check for the presence of other fields without prefix
        class_fields_without_prefix = [slot for slot in class_fields if not slot.startswith(prefix)]
        if class_fields_without_prefix:
            class_fields_without_prefix_str = "\n".join(class_fields_without_prefix)
            message = (
                f"The following fields in class {typename(cls)} do not start with the prefix '{prefix}'\n"
                f"returned by the '{typename(cls)}.get_prefix' method:\n{class_fields_without_prefix_str}"
            )
            raise RuntimeError(message)

        # Create a new dictionary of fields that start with 'prefix_' among those present in DynaconfLoader
        # This may include fields that are not specified in the settings class
        specified_fields = {k: v for k, v in loader.get_settings_dict().items() if k.startswith(prefix)}

        # Check that there are no fields in DynaconfLoader that start with 'prefix_' but are not included in cls
        if unknown_fields := [k for k in specified_fields if k not in class_fields]:
            raise RuntimeError(
                f"The following fields with prefix '{prefix}' are defined in envvars, .env or settings files\n"
                f"for the settings directory '{loader.get_settings_dir()}' but are not included\n"
                f"in the settings class: {typename(cls)} for this prefix:\n\n{cls.get_fields_str(unknown_fields)}\n\n"
                f"{loader.get_sources_str(prefix=prefix)}"
            )

        # List of required fields in cls (fields for which neither default nor default_factory is specified)
        required_fields = [
            name
            for name, field_info in cls.__dataclass_fields__.items()  # noqa
            if field_info.default is MISSING and field_info.default_factory is MISSING
        ]

        # Check for missing required fields
        if missing_fields := [k for k in required_fields if k not in specified_fields]:
            raise RuntimeError(
                f"The following fields with prefix '{prefix}' are not defined in envvars, .env or settings files\n"
                f"for the settings directory but marked as required in the settings class: {typename(cls)}\n"
                f"for the following prefix:\n\n{cls.get_fields_str(missing_fields)}\n\n"
                f"{loader.get_sources_str(prefix=prefix)}"
            )

        # TODO: Add a check for nested complex types in settings, if these are present deserialization will fail
        # TODO: Can custom deserializer that removes trailing and leading _ can be used without cyclic reference?
        result = cls(**specified_fields).build()  # noqa

        # Cache and return the result
        cls.__settings_dict[settings_dict_key] = result
        return result

    @classmethod
    def get_fields_str(cls, field_names: Sequence[str]) -> str:
        """Return a string listing the fields names in envvar/.env and settings format."""
        # Include envvar/.env and settings format
        field_formats_list = [
            f"  - '{ENVVAR_PREFIX}_{k.upper()}' (envvar/.env) or '{k}' (settings files)" for k in field_names
        ]
        result = "\n".join(field_formats_list)
        return result
