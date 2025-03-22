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
from typing import List
from cl.runtime.contexts.context import Context
from cl.runtime.contexts.context_manager import ContextManager
from cl.runtime.contexts.trial_context import TrialContext
from stubs.cl.runtime.contexts.stub_context import StubContext


def _perform_serialization_test(contexts: List[Context]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Serialize current contexts into data and then deserialize data into a ContextManager instance
    serialized_data = ContextManager.serialize_all_current()
    deserialized_context_manager = ContextManager(serialized_data)

    # Ensure the deserialized list is identical to the argument
    if not contexts:
        assert not deserialized_context_manager._all_contexts  # noqa
    else:
        assert len(contexts) == len(deserialized_context_manager._all_contexts)  # noqa
        for context, deserialized_context in zip(contexts, deserialized_context_manager._all_contexts):  # noqa
            assert context == deserialized_context


def _perform_manager_test(contexts: List[Context]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Set ContextVar=None before async task execution, get a token for restoring its previous state
    token = ContextManager.save_and_clear_state()

    try:
        # Serialize current contexts into data and then deserialize data into a ContextManager instance
        serialized_data = ContextManager._serialize_contexts(contexts)  # noqa
        with ContextManager(serialized_data):
            if contexts:
                for context in contexts:
                    current_context = type(context).current_or_none()
                    assert context == current_context
    finally:
        # Restore ContextVar to its previous state after async task execution using a token
        # from 'save_and_clear_state' whether or not an exception occurred
        ContextManager.restore_state(token)


def test_context_manager():
    """Test ContextManager class."""

    # No contexts defined
    _perform_serialization_test([])
    _perform_manager_test([])

    # Create StubContext() but do not use 'with' clause
    context_external = StubContext().build()
    _perform_manager_test([context_external])

    # Inside a single 'with StubContext()' clause
    with StubContext().build() as context_1:
        _perform_serialization_test([context_1])
    # Recreate using ContextManager
    _perform_manager_test([context_1])

    # Inside two nested 'with' clauses for the same key type StubContext
    with StubContext().build() as context_1:
        with StubContext(stub_context_id="modified_stub_context_id").build() as context_2:
            _perform_serialization_test([context_2])
    # Recreate using ContextManager
    _perform_manager_test([context_2])

    # Inside two nested 'with' clauses for different same key types
    with StubContext().build() as context_1:
        with TrialContext.with_trial_id("modified_trial_id").build() as context_2:
            _perform_serialization_test([context_1, context_2])
    # Recreate using ContextManager
    _perform_manager_test([context_1, context_2])


if __name__ == "__main__":
    pytest.main([__file__])
