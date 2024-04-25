from nose.tools import eq_
from numbers import Real
from unittest import main

from spacq.tests.tool.box import DeviceServerTestCase

from ... import voltagesource230


class ABC1234Test(DeviceServerTestCase):
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=voltagesource230.voltageSource230,
				manufacturer='Keithley', model='230 Programmable Voltage Source')

	def testSetting(self):
		"""
		Test the setting.
		"""

		abc = self.obtain_device()
		abc.reset()

		eq_(abc.setting, 'default value')

		abc.setting = 'something else'
		eq_(abc.setting, 'something else')

		try:
			abc.setting = 'another thing'
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

	def testGetValues(self):
		"""
		Obtain some values.
		"""

		abc = self.obtain_device()
		abc.reset()

		isinstance(abc.reading, Real)


if __name__ == '__main__':
	main()
