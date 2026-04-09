"""Tests standard tap features using the built-in SDK tests library."""

from hotglue_singer_sdk.testing import get_standard_tap_tests

from tap_notion.tap import TapNotion

SAMPLE_CONFIG = {"access_token": "test-token"}


# Run standard built-in tap tests from the SDK:
def test_standard_tap_tests():
    """Run standard tap tests from the SDK."""
    tests = get_standard_tap_tests(TapNotion, config=SAMPLE_CONFIG)
    for test in tests:
        test()


# TODO: Create additional tests as appropriate for your tap.
