from unittest import main

from ... import ch6_voltage_source
from .. import mock_ch6_voltage_source

from ...tests.server.test_ch6_voltage_source import ch6VoltageSourceTest


# Don't lose the real device.
real_ch6VoltageSource = ch6_voltage_source.ch6VoltageSource
is_mock = ch6VoltageSourceTest.mock


def setup():
	# Run the tests with a fake device.
	ch6_voltage_source.ch6VoltageSource = mock_ch6_voltage_source.Mockch6VoltageSource
	ch6VoltageSourceTest.mock = True

def teardown():
	# Restore the real device for any remaining tests.
	ch6_voltage_source.ch6VoltageSource = real_ch6VoltageSource
	ch6VoltageSourceTest.mock = is_mock


if __name__ == '__main__':
	main()
