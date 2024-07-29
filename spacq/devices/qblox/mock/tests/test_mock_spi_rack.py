from unittest import main

from ... import spi_rack
from .. import mock_spi_rack

from ...tests.server.test_spi_rack import ABC1234Test


# Don't lose the real device.
real_ABC1234 = spi_rack.ABC1234
is_mock = ABC1234Test.mock


def setup():
	# Run the tests with a fake device.
	spi_rack.ABC1234 = mock_spi_rack.MockABC1234
	ABC1234Test.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	spi_rack.ABC1234 = real_ABC1234
	ABC1234Test.mock = is_mock


if __name__ == '__main__':
	main()
