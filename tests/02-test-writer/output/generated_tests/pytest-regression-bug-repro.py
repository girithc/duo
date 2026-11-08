import pytest
from tqdm.std import tqdm


def test_reset_dynamic_miniters():
    """
    Test that tqdm.reset() resets auto-adjusted miniters when dynamic_miniters
    is active, rather than preserving the elevated miniters from the previous run.
    """
    with tqdm(total=1000, smoothing=0.3) as t:
        assert getattr(t, "dynamic_miniters", False) is True
        initial_miniters = t.miniters

        # Simulate fast updates or phase with large miniters adjustment
        # Dynamic miniters increases miniters when iterations complete faster than mininterval
        for _ in range(200):
            t.update(1)

        # Explicitly ensure miniters was elevated, or simulate elevated auto-adjustment
        t.miniters = 100

        t.reset(total=100)

        # After reset with dynamic_miniters active, miniters should be cleared/restarted
        # and should not remain at the elevated value (100)
        assert t.miniters != 100
        # ASSUMPTION: dynamic miniters restarts at <= 1 or initial value
        assert t.miniters <= 1 or t.miniters == initial_miniters


def test_reset_preserves_explicit_miniters():
    """
    Test that tqdm.reset() preserves explicitly provided miniters values.
    """
    explicit_val = 5
    with tqdm(total=100, miniters=explicit_val) as t:
        assert getattr(t, "dynamic_miniters", False) is False
        assert t.miniters == explicit_val

        for _ in range(20):
            t.update(1)

        t.reset(total=50)

        assert t.miniters == explicit_val
