"""pytest configuration for syn-gen tests."""

import random
import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--seed",
        action="store",
        default=None,
        type=int,
        help="Random seed for reproducibility. If not provided, a random seed is generated.",
    )


@pytest.fixture
def random_seed(request):
    """
    Fixture providing a random seed for tests.

    Uses --seed if provided, otherwise generates a random seed.
    The seed is always printed for reproducibility on failure.
    """
    seed = request.config.getoption("--seed")
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    print(f"\n=== Test seed: {seed} ===")
    return seed
