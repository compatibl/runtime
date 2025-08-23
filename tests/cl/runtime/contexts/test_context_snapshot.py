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
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.contexts.context_manager import get_active_contexts_and_ids
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.records.protocols import RecordProtocol
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime.contexts.stub_context import StubContext


def _perform_serialization_test(contexts: list[RecordProtocol]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Serialize current contexts into data and then deserialize data into a ContextSnapshot instance
    original = ContextSnapshot.capture_active()
    json_str = original.to_json()
    deserialized = ContextSnapshot.from_json(json_str)

    # Check that the contexts passed to this method match captured contexts
    # after serialization roundtrip regardless of order
    if contexts:
        not_in_contexts = [ctx for ctx in contexts if ctx not in deserialized.contexts]
        assert len(not_in_contexts) == 0
    else:
        assert not deserialized.contexts


def _perform_manager_test(contexts: list[RecordProtocol]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Capture active contexts before
    before = ContextSnapshot.capture_active()

    # Serialize current contexts into data and then deserialize data into a ContextSnapshot instance
    json_str = before.to_json()
    with ContextSnapshot.from_json(json_str):
        # Check that ContextSnapshot activated the captured contexts on __enter__
        contexts, context_ids = get_active_contexts_and_ids()
        if before.contexts:
            for context, context_id in zip(contexts, context_ids):
                active_context = active_or_none(type(context), context_id)
                assert context == active_context

    # Capture active contexts after
    after = ContextSnapshot.capture_active()

    # Check that the state was restored correctly
    if before.contexts is not None:
        assert len(before.contexts) == len(after.contexts)
        assert len([ctx for ctx in before.contexts if ctx not in after.contexts]) == 0
    else:
        assert after.contexts is None


def test_context_snapshot():
    """Test ContextSnapshot class."""

    # No contexts defined
    _perform_serialization_test([])
    _perform_manager_test([])

    # Create StubContext(...) but do not use 'with' clause
    context_external = StubContext(id="0").build()
    _perform_manager_test([context_external])

    # Inside a single 'with StubContext(...)' clause
    with activate(StubContext(id="initial_id").build()) as context_1:
        _perform_serialization_test([context_1])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_1])

    # Inside two nested 'with' clauses for the same key type StubContext
    with activate(StubContext(id="outer_modified_id").build()):
        with activate(StubContext(id="inner_modified_id").build()) as context_2:
            _perform_serialization_test([context_2])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_2])

    # Inside two nested 'with' clauses for different same key types
    with activate(StubContext(id="outer_id").build()) as context_1:
        with activate(StubDataclass(id="inner_id").build()) as context_2:
            _perform_serialization_test([context_1, context_2])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_1, context_2])


if __name__ == "__main__":
    pytest.main([__file__])
