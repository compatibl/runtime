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
from cl.runtime.contexts.trial_context import TrialContext
from cl.runtime.contexts.context_manager import activate
from stubs.cl.runtime import StubDataclass


def test_append_token():
    """Test TrialContext.add_token method."""

    assert TrialContext.get_trial() is None
    with activate(TrialContext.append_token("abc")) as trial_context_1:
        # One token in chain
        assert trial_context_1.trial_chain == ("abc",)
        assert TrialContext.get_trial() == "abc"
        with activate(TrialContext.append_token(123)) as trial_context_2:
            # Two tokens in chain
            assert trial_context_2.trial_chain == (
                "abc",
                "123",
            )
            assert TrialContext.get_trial() == "abc\\123"
        assert trial_context_1.trial_chain == ("abc",)
        assert TrialContext.get_trial() == "abc"
        with activate(TrialContext.append_token(None)) as trial_context_3:
            # One token in chain, None is ignored
            assert trial_context_3.trial_chain == ("abc",)
            assert TrialContext.get_trial() == "abc"


def test_exceptions():
    """Test TrialContext exceptions."""

    with pytest.raises(RuntimeError, match="A TrialContext must be one of the following primitive classes"):
        # Not a primitive type
        TrialContext.append_token(StubDataclass())
    with pytest.raises(RuntimeError, match="empty string"):
        # Empty string
        TrialContext.append_token("")
    with pytest.raises(RuntimeError, match="newline"):
        # Contains newline
        TrialContext.append_token("\n")
    with pytest.raises(RuntimeError, match="backslash"):
        # Contains backslash
        TrialContext.append_token("\\")


if __name__ == "__main__":
    pytest.main([__file__])
