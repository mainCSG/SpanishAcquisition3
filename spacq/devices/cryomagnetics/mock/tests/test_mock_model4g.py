from unittest import main

from ... import model4g
from .. import mock_model4g

from ...tests.server.test_model4g import Model4GTest

# Don't lose the real device.
real_Model4G = model4g.Model4G
is_mock = Model4GTest.mock


def setup():
	# Run the tests with a fake device.
	model4g.Model4G = mock_model4g.MockModel4G
	Model4GTest.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	model4g.Model4G = real_Model4G
	Model4GTest.mock = is_mock


if __name__ == '__main__':
	main()
