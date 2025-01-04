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
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb


def test_check_db_id():
    """Test 'check_db_id' method."""
    # Check for length
    BasicMongoDb.check_db_id("a" * 63)
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("a" * 64)

    # Letters, numbers and underscore are allowed
    BasicMongoDb.check_db_id("abc")
    BasicMongoDb.check_db_id("123")
    BasicMongoDb.check_db_id("abc_xyz")

    # Semicolon is allowed even though it is not in the suggested list
    BasicMongoDb.check_db_id("abc;xyz")

    # Check for space
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc xyz")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc ")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id(" xyz")

    # Check for period
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc.xyz")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc.")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id(".xyz")

    # Check for other symbols
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc:xyz")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc|xyz")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc\\xyz")
    with pytest.raises(RuntimeError):
        BasicMongoDb.check_db_id("abc/xyz")


if __name__ == "__main__":
    pytest.main([__file__])
