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
from cl.runtime.contexts.context_mixin import ContextMixin
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.contexts.trial_context import TrialContext
from stubs.cl.runtime.contexts.stub_context import StubContext


def _perform_serialization_test(contexts: List[ContextMixin]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Serialize current contexts into data and then deserialize data into a ContextSnapshot instance
    serialized_data = ContextSnapshot.serialize_current_contexts()
    deserialized_context_snapshot = ContextSnapshot(serialized_data)

    # Ensure the deserialized list is identical to the argument
    if not contexts:
        assert not deserialized_context_snapshot._all_contexts  # noqa
    else:
        assert len(contexts) == len(deserialized_context_snapshot._all_contexts)  # noqa

        # Check that the contexts passed match the contexts in ContextSnapshot regardless of order.
        not_in_contexts = [ctx for ctx in contexts if ctx not in deserialized_context_snapshot._all_contexts]  # noqa
        assert len(not_in_contexts) == 0


def _perform_manager_test(contexts: List[ContextMixin]):
    """Perform roundtrip test of serialization followed by deserialization and ensure contexts match argument."""

    # Set ContextVar=None before async task execution, get a token for restoring its previous state
    token = ContextSnapshot.save_and_clear_state()

    try:
        # Serialize current contexts into data and then deserialize data into a ContextSnapshot instance
        serialized_data = ContextSnapshot._serialize_contexts(contexts)  # noqa
        with ContextSnapshot(serialized_data):
            if contexts:
                for context in contexts:
                    current_context = type(context).current_or_none()
                    assert context == current_context
    finally:
        # Restore ContextVar to its previous state after async task execution using a token
        # from 'save_and_clear_state' whether or not an exception occurred
        ContextSnapshot.restore_state(token)


def test_context_snapshot():
    """Test ContextSnapshot class."""

    # No contexts defined
    _perform_serialization_test([])
    _perform_manager_test([])

    # Create StubContext() but do not use 'with' clause
    context_external = StubContext().build()
    _perform_manager_test([context_external])

    # Inside a single 'with StubContext()' clause
    with StubContext().build() as context_1:
        _perform_serialization_test([context_1])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_1])

    # Inside two nested 'with' clauses for the same key type StubContext
    with StubContext().build() as context_1:
        with StubContext(stub_context_id="modified_stub_context_id").build() as context_2:
            _perform_serialization_test([context_2])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_2])

    # Inside two nested 'with' clauses for different same key types
    with StubContext().build() as context_1:
        with TrialContext.append_token("modified_trial") as context_2:
            _perform_serialization_test([context_1, context_2])
    # Recreate using ContextSnapshot
    _perform_manager_test([context_1, context_2])


if __name__ == "__main__":
    pytest.main([__file__])
