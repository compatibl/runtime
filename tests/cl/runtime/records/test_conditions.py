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
from cl.runtime.records.conditions import And
from cl.runtime.records.conditions import Exists
from cl.runtime.records.conditions import Gt
from cl.runtime.records.conditions import Gte
from cl.runtime.records.conditions import In
from cl.runtime.records.conditions import Lt
from cl.runtime.records.conditions import Lte
from cl.runtime.records.conditions import Not
from cl.runtime.records.conditions import NotIn
from cl.runtime.records.conditions import Or
from cl.runtime.records.conditions import Range
from stubs.cl.runtime import StubDataclass


def test_range_condition():
    """Test Range condition with various combinations of bounds."""

    # Test with all bounds
    range_all = Range(gt=5, gte=10, lt=20, lte=15)
    assert range_all.op_gt == 5
    assert range_all.op_gte == 10
    assert range_all.op_lt == 20
    assert range_all.op_lte == 15

    # Test with only some bounds
    range_partial = Range(gt=5, lt=20)
    assert range_partial.op_gt == 5
    assert range_partial.op_gte is None
    assert range_partial.op_lt == 20
    assert range_partial.op_lte is None

    # Test with no bounds
    range_empty = Range()
    assert range_empty.op_gt is None
    assert range_empty.op_gte is None
    assert range_empty.op_lt is None
    assert range_empty.op_lte is None

    # Test with string values
    range_string = Range(gt="a", lte="z")
    assert range_string.op_gt == "a"
    assert range_string.op_lte == "z"


def test_and_condition():
    """Test And condition with various combinations of conditions."""

    # Test with multiple conditions
    and_condition = And(5, 10, 15)
    assert len(and_condition.op_and) == 3
    assert and_condition.op_and == (5, 10, 15)

    # Test with single condition
    and_single = And(42)
    assert len(and_single.op_and) == 1
    assert and_single.op_and == (42,)

    # Test with no conditions
    and_empty = And()
    assert len(and_empty.op_and) == 0
    assert and_empty.op_and == ()

    # Test with mixed types
    range_cond = Range(gt=5, lt=10)
    and_mixed = And(5, range_cond, 42)
    assert len(and_mixed.op_and) == 3
    assert and_mixed.op_and[0] == 5
    assert isinstance(and_mixed.op_and[1], Range)
    assert and_mixed.op_and[2] == 42


def test_or_condition():
    """Test Or condition with various combinations of conditions."""

    # Test with multiple conditions
    or_condition = Or(5, 10, 15)
    assert len(or_condition.op_or) == 3
    assert or_condition.op_or == (5, 10, 15)

    # Test with single condition
    or_single = Or(42)
    assert len(or_single.op_or) == 1
    assert or_single.op_or == (42,)

    # Test with no conditions
    or_empty = Or()
    assert len(or_empty.op_or) == 0
    assert or_empty.op_or == ()

    # Test with mixed types
    range_cond = Range(gt=5, lt=10)
    or_mixed = Or(5, range_cond, 42)
    assert len(or_mixed.op_or) == 3
    assert or_mixed.op_or[0] == 5
    assert isinstance(or_mixed.op_or[1], Range)
    assert or_mixed.op_or[2] == 42


def test_not_condition():
    """Test Not condition with various values."""

    # Test with primitive value
    not_primitive = Not(42)
    assert not_primitive.op_not == 42

    # Test with string value
    not_string = Not("test")
    assert not_string.op_not == "test"

    # Test with condition
    range_cond = Range(gt=5, lt=10)
    not_condition = Not(range_cond)
    assert isinstance(not_condition.op_not, Range)
    assert not_condition.op_not == range_cond

    # Test with None
    not_none = Not(None)
    assert not_none.op_not is None


def test_exists_condition():
    """Test Exists condition with boolean values."""

    # Test with True
    exists_true = Exists(True)
    assert exists_true.op_exists is True

    # Test with False
    exists_false = Exists(False)
    assert exists_false.op_exists is False

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of Exists operator has type"):
        Exists(42)

    with pytest.raises(RuntimeError, match="Argument of Exists operator has type"):
        Exists("test")

    with pytest.raises(RuntimeError, match="Argument of Exists operator has type"):
        Exists(None)


def test_in_condition():
    """Test In condition with various sequences."""

    # Test with list
    in_list = In([1, 2, 3, 4, 5])
    assert in_list.op_in == (1, 2, 3, 4, 5)

    # Test with tuple
    in_tuple = In((1, 2, 3))
    assert in_tuple.op_in == (1, 2, 3)

    # Test with string sequence
    in_strings = In(["a", "b", "c"])
    assert in_strings.op_in == ("a", "b", "c")

    # Test with empty sequence
    in_empty = In([])
    assert in_empty.op_in == ()

    # Test with single element
    in_single = In([42])
    assert in_single.op_in == (42,)

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of In operator has type"):
        In(42)

    with pytest.raises(RuntimeError, match="Argument of In operator has type"):
        In("not a sequence")

    with pytest.raises(RuntimeError, match="Argument of In operator has type"):
        In(None)


def test_not_in_condition():
    """Test NotIn condition with various sequences."""

    # Test with list
    not_in_list = NotIn([1, 2, 3, 4, 5])
    assert not_in_list.op_nin == (1, 2, 3, 4, 5)

    # Test with tuple
    not_in_tuple = NotIn((1, 2, 3))
    assert not_in_tuple.op_nin == (1, 2, 3)

    # Test with string sequence
    not_in_strings = NotIn(["a", "b", "c"])
    assert not_in_strings.op_nin == ("a", "b", "c")

    # Test with empty sequence
    not_in_empty = NotIn([])
    assert not_in_empty.op_nin == ()

    # Test with single element
    not_in_single = NotIn([42])
    assert not_in_single.op_nin == (42,)

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of NotIn operator has type"):
        NotIn(42)

    with pytest.raises(RuntimeError, match="Argument of NotIn operator has type"):
        NotIn("not a sequence")

    with pytest.raises(RuntimeError, match="Argument of NotIn operator has type"):
        NotIn(None)


def test_gt_condition():
    """Test Gt condition with various primitive values."""

    # Test with integer
    gt_int = Gt(5)
    assert gt_int.op_gt == 5

    # Test with float
    gt_float = Gt(3.14)
    assert gt_float.op_gt == 3.14

    # Test with string
    gt_string = Gt("test")
    assert gt_string.op_gt == "test"

    # Test with boolean
    gt_bool = Gt(True)
    assert gt_bool.op_gt is True

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of Gt operator has type"):
        Gt([1, 2, 3])

    with pytest.raises(RuntimeError, match="Argument of Gt operator has type"):
        Gt({"key": "value"})

    with pytest.raises(RuntimeError, match="Argument of Gt operator has type"):
        Gt(None)


def test_gte_condition():
    """Test Gte condition with various primitive values."""

    # Test with integer
    gte_int = Gte(5)
    assert gte_int.op_gte == 5

    # Test with float
    gte_float = Gte(3.14)
    assert gte_float.op_gte == 3.14

    # Test with string
    gte_string = Gte("test")
    assert gte_string.op_gte == "test"

    # Test with boolean
    gte_bool = Gte(False)
    assert gte_bool.op_gte is False

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of Gte operator has type"):
        Gte([1, 2, 3])

    with pytest.raises(RuntimeError, match="Argument of Gte operator has type"):
        Gte({"key": "value"})

    with pytest.raises(RuntimeError, match="Argument of Gte operator has type"):
        Gte(None)


def test_lt_condition():
    """Test Lt condition with various primitive values."""

    # Test with integer
    lt_int = Lt(5)
    assert lt_int.op_lt == 5

    # Test with float
    lt_float = Lt(3.14)
    assert lt_float.op_lt == 3.14

    # Test with string
    lt_string = Lt("test")
    assert lt_string.op_lt == "test"

    # Test with boolean
    lt_bool = Lt(True)
    assert lt_bool.op_lt is True

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of Lt operator has type"):
        Lt([1, 2, 3])

    with pytest.raises(RuntimeError, match="Argument of Lt operator has type"):
        Lt({"key": "value"})

    with pytest.raises(RuntimeError, match="Argument of Lt operator has type"):
        Lt(None)


def test_lte_condition():
    """Test Lte condition with various primitive values."""

    # Test with integer
    lte_int = Lte(5)
    assert lte_int.op_lte == 5

    # Test with float
    lte_float = Lte(3.14)
    assert lte_float.op_lte == 3.14

    # Test with string
    lte_string = Lte("test")
    assert lte_string.op_lte == "test"

    # Test with boolean
    lte_bool = Lte(False)
    assert lte_bool.op_lte is False

    # Test with invalid type (should raise RuntimeError)
    with pytest.raises(RuntimeError, match="Argument of Lte operator has type"):
        Lte([1, 2, 3])

    with pytest.raises(RuntimeError, match="Argument of Lte operator has type"):
        Lte({"key": "value"})

    with pytest.raises(RuntimeError, match="Argument of Lte operator has type"):
        Lte(None)


def test_nested_conditions():
    """Test complex nested conditions."""

    # Create a complex nested condition
    range_cond = Range(gt=5, lt=10)
    gt_cond = Gt(3)
    gte_cond = Gte(5)
    lt_cond = Lt(15)
    lte_cond = Lte(12)
    in_cond = In([1, 2, 3])
    exists_cond = Exists(True)

    # And with nested conditions
    and_nested = And(range_cond, gt_cond, gte_cond, in_cond, exists_cond)
    assert len(and_nested.op_and) == 5
    assert isinstance(and_nested.op_and[0], Range)
    assert isinstance(and_nested.op_and[1], Gt)
    assert isinstance(and_nested.op_and[2], Gte)
    assert isinstance(and_nested.op_and[3], In)
    assert isinstance(and_nested.op_and[4], Exists)

    # Or with nested conditions
    or_nested = Or(range_cond, lt_cond, lte_cond, in_cond, exists_cond)
    assert len(or_nested.op_or) == 5
    assert isinstance(or_nested.op_or[0], Range)
    assert isinstance(or_nested.op_or[1], Lt)
    assert isinstance(or_nested.op_or[2], Lte)
    assert isinstance(or_nested.op_or[3], In)
    assert isinstance(or_nested.op_or[4], Exists)

    # Not with nested condition
    not_nested = Not(gt_cond)
    assert isinstance(not_nested.op_not, Gt)

    # Complex nesting
    complex_condition = And(Or(range_cond, gt_cond, lt_cond), Not(exists_cond), And(gte_cond, lte_cond, 1, 2, 3))
    assert len(complex_condition.op_and) == 3
    assert isinstance(complex_condition.op_and[0], Or)
    assert isinstance(complex_condition.op_and[1], Not)
    assert isinstance(complex_condition.op_and[2], And)


def test_condition_with_stub_dataclass():
    """Test conditions with stub dataclass instances."""

    # Create a stub dataclass instance
    stub_instance = StubDataclass()

    # Test Range with stub instance - this should work since Range doesn't check primitives
    range_stub = Range(gt=stub_instance)
    assert range_stub.op_gt == stub_instance

    # Test comparison operators with stub instance - these should fail since StubDataclass is not primitive
    with pytest.raises(RuntimeError, match="Argument of Gt operator has type"):
        Gt(stub_instance)

    with pytest.raises(RuntimeError, match="Argument of Gte operator has type"):
        Gte(stub_instance)

    with pytest.raises(RuntimeError, match="Argument of Lt operator has type"):
        Lt(stub_instance)

    with pytest.raises(RuntimeError, match="Argument of Lte operator has type"):
        Lte(stub_instance)

    # Test In with stub instances - this should work since In accepts any sequence
    in_stub = In([stub_instance, stub_instance])
    assert len(in_stub.op_in) == 2
    assert in_stub.op_in[0] == stub_instance
    assert in_stub.op_in[1] == stub_instance

    # Test And with stub instance
    and_stub = And(stub_instance, 42)
    assert len(and_stub.op_and) == 2
    assert and_stub.op_and[0] == stub_instance
    assert and_stub.op_and[1] == 42


if __name__ == "__main__":
    pytest.main([__file__])
