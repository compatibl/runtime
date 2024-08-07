# Copyright (C) 2003-present CompatibL. All rights reserved.
#
# This file contains valuable trade secrets and may be copied, stored, used,
# or distributed only in compliance with the terms of a written commercial
# license from CompatibL and with the inclusion of this copyright notice.

from cl.runtime.records.dataclasses_extensions import field
from cl.runtime.records.dataclasses_extensions import missing
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class BaseTypeInfo:
    """Base type info."""

    name: str = missing()
    """Name of type."""

    module: str = missing()
    """Module of type."""

    label: str = missing()
    """Label of type."""
