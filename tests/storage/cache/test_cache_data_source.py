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
import cl.runtime as rt
import cl.runtime_samples as samples


class TestCacheDataSource:
    """Tests for CacheDataSource class."""

    def test_smoke(self):
        """Smoke test."""

        # Create data source and dataset
        data_source = rt.CacheDataSource()
        data_set = "sample"

        # Create test record and populate with sample data
        context = rt.Context()
        record = samples.RecordSample()
        record.populate_with_sample_data(context)
        pk = record.to_pk()
        record_dict = record.to_dict()

        # Test saving and loading
        data_source.save_one(record, data_set)
        loaded_record = samples.RecordSample()
        data_source.load_one(pk, data_set, out=loaded_record)
        loaded_record_dict = loaded_record.to_dict()
        assert loaded_record_dict == record_dict


if __name__ == '__main__':
    pytest.main([__file__])