from unittest import main

from ... import dm34401a
from .. import mock_dm34401a

from ...tests.server.test_dm34401a import DM34401ATest


# Don't lose the real device.
real_DM34401A = dm34401a.DM34401A
is_mock = DM34401ATest.mock


def setup():
	# Run the tests with a fake device.
	dm34401a.DM34401A = mock_dm34401a.MockDM34401A
	DM34401ATest.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	dm34401a.DM34401A = real_DM34401A
	DM34401ATest.mock = is_mock


if __name__ == '__main__':
	main()
