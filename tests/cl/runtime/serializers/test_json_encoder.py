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

import pytest
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.serializers.json_encoders import JsonEncoders

_DICT_SAMPLE = {
    "str": "abc",
    "str_brace": "{",
    "str_bracket": "[",
    "str_double_quote": '"',
    "str_single_quote": "'",
    "int": 1,
    "float": 1.0,
}

_LIST_SAMPLE = [
    "abc",
    "{",
    "[",
    '"',
    "'",
    1,
    1.0,
]

_SAMPLES = [
    "abc",
    1,
    1.0,
    # dt.date(2023, 5, 1),
    _DICT_SAMPLE,
    [_DICT_SAMPLE, _DICT_SAMPLE],
    _LIST_SAMPLE,
    [_LIST_SAMPLE, _LIST_SAMPLE],
]

_ENCODERS = [
    ("default", JsonEncoders.DEFAULT),
    ("compact", JsonEncoders.COMPACT),
]


def test_roundtrip():
    """Test DataSerializer.to_json method."""

    for encoder_name, encoder in _ENCODERS:
        for sample in _SAMPLES:
            guard = RegressionGuard(prefix=encoder_name).build()

            # Test encoding
            encoded = encoder.encode(sample)
            guard.write(encoded)

            # Test decoding
            decoded = encoder.decode(encoded)
            assert decoded == sample

    RegressionGuard().build().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
