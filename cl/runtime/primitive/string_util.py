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

import hashlib
import re
from typing import TypeGuard, Iterable

from cl.runtime.log.exceptions.user_error import UserError

_DISALLOWED_DELIMITERS = {
    "\\": "Backslash",
    ";": "Semicolon",
}
"""These delimiters are not allowed in the text."""

_WHITESPACE_RE = re.compile(r"\s+")
"""Regex for whitespace replacement."""


class StringUtil:
    """Utilities for string, other than case conversion which is in CaseUtil."""

    @classmethod
    def is_empty(cls, value: str | None) -> bool:
        """Returns true if the string is None or ''."""
        return value is None or value == ""

    @classmethod
    def is_not_empty(cls, value: str | None) -> TypeGuard[str]:
        """Returns true if the string is not None or ''."""
        return value is not None and value != ""

    @classmethod
    def digest(
            cls,
            text: str,
            *,
            text_params: Iterable[str] | None = None,
            hash_params: Iterable[str] | None = None,
    ) -> str:
        """
        Return digest in one of the following two formats:
        Format 1: shortened_text (text_param_1, text_param_2, ...)
        Format 2: shortened_text (text_param_1, text_param_2, ..., md5)
        The text is shortened only if it is multiline or exceeds 80 characters.
        Text params are included in the digest and hash params are included in MD5.
        """

        # Shorten text if required, this also makes it single line
        if "\n" in text or len(text) > 80:
            # Get the first 160 characters, replace all whitespace by a single space and then truncate to 80
            digest = text[:160].strip()
            digest = _WHITESPACE_RE.sub(" ", digest).strip()
            digest = digest[:80].strip()
            is_truncated = True
        else:
            digest = text
            is_truncated = False

        # Prune empty text parameters and create a comma-delimited string
        text_params = tuple(x for x in text_params if x is not None) if text_params else None
        text_params_str = ", ".join(str(x) for x in text_params) if text_params else ""

        # Prune empty hash parameters and create a comma-delimited string
        hash_params = tuple(x for x in hash_params if x is not None) if hash_params else None
        hash_params_str = "".join(str(x) for x in hash_params) if hash_params else ""

        if is_truncated or hash_params_str:
            # Append MD5 hash in hexadecimal format if the text is truncated or hash_params are present
            md5_input = f"{text}{hash_params_str}"
            md5_hash = StringUtil.md5_hex(md5_input)
            if text_params_str:
                digest = f"{digest} ({text_params_str}, {md5_hash})"
            else:
                digest = f"{digest} ({md5_hash})"
        else:
            # Otherwise append text_params (if present) without hash
            if text_params_str:
                digest = f"{digest} ({text_params_str})"

        delimiters = [name for sub, name in _DISALLOWED_DELIMITERS.items() if sub in digest]
        if delimiters:
            delimiters_str = "\n".join(delimiters)
            raise UserError(
                f"A digest contains disallowed delimiters:\n"
                f"Disallowed delimiters found: {delimiters_str}\n"
                f"Digest: {digest}\n"
            )

        return digest

    @classmethod
    def md5_hex(cls, value: str | None) -> str:
        """Return MD5 hash in hexadecimal format after converting to lowercase and removing all whitespace."""
        return cls._md5(value).hexdigest()

    @classmethod
    def _md5(cls, value: str | None):
        """Return MD5 hash object after converting to lowercase and removing all whitespace."""

        # Convert to lowercase and remove all whitespace including EOL for any OS
        value = value.lower()
        value = value.replace(" ", "").replace("\n", "").replace("\r", "")

        # Encode to bytes using UTF-8 and get the MD5 hash in hexadecimal format
        result = hashlib.md5(value.encode("utf-8"))
        return result
