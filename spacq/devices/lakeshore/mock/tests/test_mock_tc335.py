from unittest import main

from ... import tc335
from .. import mock_tc335

from ...tests.server.test_tc335 import TC335Test


# Don't lose the real device.
real_TC335 = tc335.TC335
is_mock = TC335Test.mock


def setup():
	# Run the tests with a fake device.
	tc335.TC335 = mock_tc335.MockTC335
	TC335Test.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	tc335.TC335 = real_TC335
	TC335Test.mock = is_mock


if __name__ == '__main__':
	main()
