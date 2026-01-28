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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite_key import StubDataclassCompositeKey

from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers_key import StubHandlersKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey

_KEY_SAMPLES = [
    StubDataclassKey().build(),
    StubDataclassCompositeKey().build(),
    StubDataclassPrimitiveFieldsKey().build(),
    StubDataclassPolymorphicKey().build(),
]

_EXCEPTION_SAMPLES = [
    StubDataclassKey(),  # Build is not called, not frozen as a result
]


def test_hashing_basics():
    """Test hashing of frozen and unfrozen types."""

    # Test hashing of key sample types
    for sample in _KEY_SAMPLES:
        hash(sample)

    # Expected exceptions
    for sample in _EXCEPTION_SAMPLES:
        # Attempt hashing
        with pytest.raises(RuntimeError, match="because it is not frozen"):
            hash(sample)


def test_key_hash():
    """Test KeyMixin.__hash__ method directly."""
    # Test that frozen keys are hashable
    key_a = StubDataclassKey(id="a").build()
    key_b = StubDataclassKey(id="b").build()
    key_a_duplicate = StubDataclassKey(id="a").build()

    # Same key should have same hash
    assert hash(key_a) == hash(key_a_duplicate)
    # Different keys should have different hashes (usually, but not guaranteed)
    assert hash(key_a) != hash(key_b)

    # Test that unfrozen keys raise error
    unfrozen_key = StubDataclassKey(id="a")
    with pytest.raises(RuntimeError, match="not frozen"):
        hash(unfrozen_key)


def test_key_equality():
    """Test KeyMixin.__eq__ method."""
    # Test equal keys
    key_a1 = StubDataclassKey(id="a").build()
    key_a2 = StubDataclassKey(id="a").build()
    assert key_a1 == key_a2

    # Test different keys
    key_b = StubDataclassKey(id="b").build()
    assert key_a1 != key_b

    # Test equality with different types
    other_key = StubHandlersKey(stub_id="a").build()
    assert key_a1 != other_key

    # Test equality with non-KeyMixin objects
    assert key_a1 != "not a key"
    assert key_a1 != 123
    # Test that key is not equal to None (but key itself is not None)
    assert (key_a1 != None) is True  # noqa: E711


def test_key_in_dict():
    """Test using KeyMixin as dictionary keys."""
    key_a = StubDataclassKey(id="a").build()
    key_b = StubDataclassKey(id="b").build()
    key_a_duplicate = StubDataclassKey(id="a").build()

    # Create dictionary with keys
    my_dict = {key_a: "value_a", key_b: "value_b"}

    # Test retrieval
    assert my_dict[key_a] == "value_a"
    assert my_dict[key_b] == "value_b"

    # Test that duplicate key accesses same value
    assert my_dict[key_a_duplicate] == "value_a"

    # Test updating
    my_dict[key_a] = "updated_value"
    assert my_dict[key_a_duplicate] == "updated_value"


def test_key_in_set():
    """Test using KeyMixin in sets."""
    key_a = StubDataclassKey(id="a").build()
    key_b = StubDataclassKey(id="b").build()
    key_a_duplicate = StubDataclassKey(id="a").build()

    # Create set with keys
    my_set = {key_a, key_b, key_a_duplicate}

    # Duplicate keys should be deduplicated
    assert len(my_set) == 2
    assert key_a in my_set
    assert key_b in my_set
    assert key_a_duplicate in my_set


def test_key_hash_consistency():
    """Test that hash is consistent across multiple calls."""
    key = StubDataclassKey(id="test").build()

    # Hash should be consistent
    hash1 = hash(key)
    hash2 = hash(key)
    assert hash1 == hash2


def test_key_hash_equality_consistency():
    """Test that equal keys have equal hashes (hash contract)."""
    key_a1 = StubDataclassKey(id="a").build()
    key_a2 = StubDataclassKey(id="a").build()

    # If two objects are equal, they must have the same hash
    assert key_a1 == key_a2
    assert hash(key_a1) == hash(key_a2)


def test_key_with_composite_fields():
    """Test hash and equality with composite keys (keys containing nested keys)."""
    # Create keys with same values across all fields including nested keys
    # Use separate instances to test that equality works by value, not reference
    embedded_key_1a = StubDataclassKey(id="key1").build()
    embedded_key_1b = StubDataclassKey(id="key1").build()  # Same value, different instance
    embedded_key_2a = StubDataclassKey(id="key2").build()
    embedded_key_2b = StubDataclassKey(id="key2").build()  # Same value, different instance

    key1 = StubDataclassCompositeKey(
        primitive="test",
        embedded_1=embedded_key_1a,
        embedded_2=embedded_key_2a,
    ).build()
    key2 = StubDataclassCompositeKey(
        primitive="test",
        embedded_1=embedded_key_1b,  # Different instance, same value
        embedded_2=embedded_key_2b,  # Different instance, same value
    ).build()

    # Create key with different primitive value
    key3 = StubDataclassCompositeKey(
        primitive="different",
        embedded_1=embedded_key_1a,
        embedded_2=embedded_key_2a,
    ).build()

    # Same keys should be equal and have same hash (even with different instances)
    assert key1 == key2
    assert hash(key1) == hash(key2)

    # Different keys should not be equal
    assert key1 != key3

    # Test that nested keys are considered in hash
    embedded_key_3 = StubDataclassKey(id="key3").build()
    key4 = StubDataclassCompositeKey(
        primitive="test",
        embedded_1=embedded_key_3,  # Different embedded key value
        embedded_2=embedded_key_2a,
    ).build()
    assert key1 != key4


if __name__ == "__main__":
    pytest.main([__file__])
