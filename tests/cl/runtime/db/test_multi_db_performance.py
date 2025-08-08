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
import time
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from stubs.cl.runtime import StubDataclassPrimitiveFields


@pytest.mark.skip("Performance test.")
def test_performance(multi_db_fixture):
    """Test performance of save/load methods."""
    n = 1000
    samples = [StubDataclassPrimitiveFields(key_str_field=f"key{i}") for i in range(n)]
    sample_keys = [sample.get_key() for sample in samples]

    print(f">>> Test stub type: {StubDataclassPrimitiveFields.__name__}, {n=}.")
    start_time = time.time()
    active(DataSource).save_many(samples)
    end_time = time.time()

    print(f"Save many bulk: {end_time - start_time}s.")

    start_time = time.time()
    for sample in samples:
        active(DataSource).save_one(sample)
    end_time = time.time()
    print(f"Save many one by one: {end_time - start_time}s.")

    start_time = time.time()
    list(active(DataSource).load_many(sample_keys))
    end_time = time.time()
    print(f"Load many bulk: {end_time - start_time}s.")

    start_time = time.time()
    for key in sample_keys:
        active(DataSource).load_one(key)
    end_time = time.time()
    print(f"Load many one by one: {end_time - start_time}s.")


if __name__ == "__main__":
    pytest.main([__file__])
