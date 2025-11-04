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
from cl.runtime.contexts.context_manager import active
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.stat.draw import Draw


def test_context():
    """Test Draw context."""

    assert active_or_none(Draw) is None
    with activate(Draw(draw_index=1).build()) as draw_1:
        # One token in chain
        assert draw_1.draw_id == "1"
        assert active(Draw).draw_id == "1"
        with activate(Draw(draw_index=2).build()) as draw_12:
            # Two tokens in chain
            assert draw_12.draw_id == "1.2"
            assert active(Draw).draw_id == "1.2"
        assert active(Draw).draw_id == "1"
        with activate(Draw(draw_index=3).build()) as draw_13:
            # Two tokens in chain
            assert draw_13.draw_id == "1.3"
            assert active(Draw).draw_id == "1.3"
    assert active_or_none(Draw) is None


def test_exceptions():
    """Test Draw exceptions."""

    not_int_msg = "is not an int"
    required_msg = "Required field is None or an empty primitive type"
    negative_msg = "Draw index is negative"
    with pytest.raises(RuntimeError, match=not_int_msg):
        # Not an int
        Draw(draw_index="1").build()  # noqa
    with pytest.raises(RuntimeError, match=required_msg):
        # Empty string
        Draw(draw_index="").build()  # noqa
    with pytest.raises(RuntimeError, match=required_msg):
        # None
        Draw(draw_index=None).build()  # noqa
    with pytest.raises(RuntimeError, match=negative_msg):
        # Negative
        Draw(draw_index=-1).build()


if __name__ == "__main__":
    pytest.main([__file__])
