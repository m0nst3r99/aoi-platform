"""Synthetic test policy only; not production defaults."""
from models import Limits

TEST_LIMITS = Limits('windows-runner-test-v1', 1024*1024, 65536, 65536,
                     98304, 4096, 5000, 3000, 128*1024*1024, 384*1024*1024, 8)
