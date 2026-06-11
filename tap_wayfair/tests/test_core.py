"""Tests standard tap features using the built-in SDK tests library."""

import datetime
import json
import os

import pytest
from hotglue_singer_sdk.testing import get_standard_tap_tests

from tap_wayfair.tap import TapWayfair

_SECRETS_CONFIG = os.path.join(os.path.dirname(__file__), "../../.secrets/config.json")


@pytest.fixture
def sample_config():
    if not os.path.exists(_SECRETS_CONFIG):
        pytest.skip("Secrets file not found; skipping integration tests.")
    with open(_SECRETS_CONFIG) as config_file:
        config = json.load(config_file)
    return {
        **config,
        "start_date": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


def test_standard_tap_tests(sample_config):
    tests = get_standard_tap_tests(TapWayfair, config=sample_config)
    for test in tests:
        test()
