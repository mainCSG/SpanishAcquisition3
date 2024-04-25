import logging
log = logging.getLogger(__name__)

from unittest import main

from spacq.interface.units import Quantity
from spacq.tests.tool.box import DeviceServerTestCase

from ... import ch6_voltage_source


class ch6VoltageSourceTest(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=ch6_voltage_source.ch6VoltageSource,
				manufacturer='IQC', model='Six channel voltage source')

	def testCalibrate(self):
		"""
		Self-calibrate all the ports.
		"""

		vsrc = self.obtain_device()

		for port in vsrc.ports:
			port.apply_settings(calibrate=True)

	def testSetVoltages(self):
		"""
		Set voltages on all the ports.

		Note: Verification should also be done manually based on the voltage source output.
		"""

		vsrc = self.obtain_device()

		test_voltages = list(range(-10, 10 + 1, 2)) + list(range(5, 0, -1))

		for port, voltage in zip(range(6), test_voltages):
			vsrc.ports[port].voltage = Quantity(voltage, 'V')


if __name__ == '__main__':
	main()
