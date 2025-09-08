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

import dataclasses
from typing import Callable
from typing import TypeVar

TDefault = TypeVar("TDefault")
TDefaultFactory = Callable[[], TDefault]


def required(
    *,
    default: TDefault | None = None,
    default_factory: TDefaultFactory | None = None,
    init: bool = True,
    repr: bool = True,  # noqa
    compare: bool = True,
    name: str | None = None,  # TODO: Review use when trailing _ is removed automatically
    label: str | None = None,
    subtype: str | None = None,
    formatter: str | None = None,
    descending: bool | None = None,
) -> TDefault:
    """
    Use to specify a field in dataclass that can be omitted in __init__ but must be set before validation.

    Args:
        default: Default value for primitive types, None if not specified
        default_factory: Factory to generate default value for mutable types
        init: True by default, if False the field is omitted from __init__ params
        repr: True by default, if False the field is omitted from debugger representation
        compare: True by default, if False the field is omitted from comparison functions
        name: Override field name in REST (label will be titleized version of this parameter unless set directly)
        label: Override titleized name in UI
        subtype: Subtype within the Python type, for example 'long' for int Python type
        formatter: Standard formatter name (without curly brackets) or raw Python format string (in curly brackets)
        descending: If True, field order in DB index will be DESCENDING rather than the default (ASCENDING)
    """
    # Create metadata dict, include only those fields that are not None, set to None if no such fields
    metadata = {
        "optional": False,
        "name": name,
        "label": label,
        "subtype": subtype,
        "formatter": formatter,  # TODO: switch to formatter in other places as format causes Python warnings
        "descending": descending,
    }

    if default_factory is None:
        return dataclasses.field(
            default=default,
            init=init,
            repr=repr,
            compare=compare,
            metadata=metadata,
        )
    elif default is None:
        return dataclasses.field(
            default_factory=default_factory,
            init=init,
            repr=repr,
            compare=compare,
            metadata=metadata,
        )
    else:
        raise RuntimeError(
            f"Params default={default} and default_factory={default_factory} "
            f"are mutually exclusive but both are specified."
        )


def optional(
    *,
    default: TDefault | None = None,
    default_factory: TDefaultFactory | None = None,
    init: bool = True,
    repr: bool = True,  # noqa
    compare: bool = True,
    name: str | None = None,  # TODO: Review use when trailing _ is removed automatically
    label: str | None = None,
    subtype: str | None = None,
    formatter: str | None = None,
    descending: bool | None = None,
) -> TDefault:
    """
    Use to specify an optional field in dataclass with additional parameters.

    Notes:
        If no parameters are necessary other than 'default', the default value can be
        specified in dataclass definition instead of using this method.

    Args:
        default: Default value for primitive types, None if not specified
        default_factory: Factory to generate default value for mutable types
        init: True by default, if False the field is omitted from __init__ params
        repr: True by default, if False the field is omitted from debugger representation
        compare: True by default, if False the field is omitted from comparison functions
        name: Override field name in REST (label will be titleized version of this parameter unless set directly)
        label: Override titleized name in UI
        subtype: Subtype within the Python type, for example 'long' for int Python type
        formatter: Standard formatter name (without curly brackets) or raw Python format string (in curly brackets)
        descending: If True, field order in DB index will be DESCENDING rather than the default (ASCENDING)
    """
    # Create metadata dict, include only those fields that are not None, set to None if no such fields
    metadata = {
        "optional": True,
        "name": name,
        "label": label,
        "subtype": subtype,
        "formatter": formatter,  # TODO: switch to formatter in other places as format causes Python warnings
        "descending": descending,
    }

    if default_factory is None:
        return dataclasses.field(
            default=default,
            init=init,
            repr=repr,
            compare=compare,
            metadata=metadata,
        )
    elif default is None:
        return dataclasses.field(
            default_factory=default_factory,
            init=init,
            repr=repr,
            compare=compare,
            metadata=metadata,
        )
    else:
        raise RuntimeError(
            f"Params default={default} and default_factory={default_factory} "
            f"are mutually exclusive but both are specified."
        )
