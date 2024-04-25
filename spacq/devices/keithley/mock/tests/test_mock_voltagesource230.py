from unittest import main

from ... import voltagesource230
from .. import mock_voltagesource230

from ...tests.server.test_voltagesource230 import voltageSource230Test


# Don't lose the real device.
real_voltageSource230 = voltagesource230.voltageSource230
is_mock = voltageSource230Test.mock


def setup():
	# Run the tests with a fake device.
	voltagesource230.voltageSource230 = mock_voltagesource230.MockvoltageSource230
	voltageSource230Test.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	voltagesource230.voltageSource230 = real_voltageSource230
	voltageSource230Test.mock = is_mock


if __name__ == '__main__':
	main()
