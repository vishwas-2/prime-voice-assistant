"""
Sample tests to verify testing framework setup.

This file contains basic tests to verify that:
1. pytest is configured correctly
2. Hypothesis (property-based testing) is working
3. Test markers are recognized
4. Test discovery is functioning
"""

import pytest
from hypothesis import given, strategies as st


class TestPytestSetup:
    """Verify pytest is configured correctly."""
    
    def test_basic_assertion(self):
        """Basic test to verify pytest can run tests."""
        assert True
    
    def test_fixture_support(self, tmp_path):
        """Verify pytest fixtures work correctly."""
        # tmp_path is a built-in pytest fixture
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, PRIME!")
        assert test_file.read_text() == "Hello, PRIME!"
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Verify unit test marker is recognized."""
        assert 1 + 1 == 2
    
    @pytest.mark.property
    def test_property_marker(self):
        """Verify property test marker is recognized."""
        assert 2 * 2 == 4


class TestHypothesisSetup:
    """Verify Hypothesis property-based testing is working."""
    
    @given(st.integers())
    def test_integer_addition_commutative(self, x):
        """Property: Integer addition is commutative."""
        # For any integer x, x + 0 = x
        assert x + 0 == x
    
    @given(st.integers(min_value=0, max_value=1000))
    def test_integer_multiplication_identity(self, x):
        """Property: Multiplication by 1 is identity."""
        assert x * 1 == x
    
    @given(st.text())
    def test_string_concatenation_length(self, s):
        """Property: Concatenating a string with itself doubles its length."""
        result = s + s
        assert len(result) == 2 * len(s)
    
    @given(st.lists(st.integers()))
    def test_list_reversal_involution(self, lst):
        """Property: Reversing a list twice returns the original list."""
        assert list(reversed(list(reversed(lst)))) == lst
    
    @given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
    def test_multiplication_commutative(self, a, b):
        """Property: Multiplication is commutative."""
        assert a * b == b * a


class TestTestStructure:
    """Verify test directory structure is accessible."""
    
    def test_can_import_from_prime(self):
        """Verify we can import from the prime package."""
        try:
            import prime
            assert hasattr(prime, '__name__')
        except ImportError:
            pytest.fail("Cannot import prime package")
    
    def test_can_import_models(self):
        """Verify we can import data models."""
        try:
            from prime.models import Session, Intent, Command
            assert Session is not None
            assert Intent is not None
            assert Command is not None
        except ImportError as e:
            pytest.fail(f"Cannot import models: {e}")


@pytest.mark.property
class TestPropertyBasedTestingFeatures:
    """Demonstrate property-based testing features for PRIME."""
    
    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_score_range(self, confidence):
        """Property: Confidence scores should be between 0 and 1."""
        assert 0.0 <= confidence <= 1.0
    
    @given(st.text(min_size=1))
    def test_non_empty_string_has_length(self, text):
        """Property: Non-empty strings have positive length."""
        assert len(text) > 0
    
    @given(st.lists(st.text(), min_size=1))
    def test_list_first_element_accessible(self, lst):
        """Property: First element of non-empty list is accessible."""
        assert lst[0] is not None or lst[0] == ""


if __name__ == "__main__":
    # Allow running this file directly for quick verification
    pytest.main([__file__, "-v"])
