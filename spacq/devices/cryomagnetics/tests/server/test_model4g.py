from nose.tools import eq_
from unittest import main
from time import sleep

from spacq.tests.tool.box import DeviceServerTestCase
from spacq.interface.units import Quantity, IncompatibleDimensions

from ... import model4g

"""
model4g:
-go over code looking for missed cases.
"""

class Model4GTest(DeviceServerTestCase):
	
	channel_to_test = 1
	
	def obtain_device(self):
		return DeviceServerTestCase.obtain_device(self, impl=model4g.Model4G,
				manufacturer='Cryomagnetics', model='Model 4G')

	def testLimits(self):
		"""
		Test the limits.
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		# Test setting the high limit.

		chanctrler.high_limit = Quantity('50 G')
		eq_(chanctrler.high_limit, Quantity('50 G'))

		try:
			chanctrler.high_limit = 55
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'
		
		# ...and the low limit.
		
		chanctrler.low_limit = Quantity('40 G')
		eq_(chanctrler.low_limit, Quantity('40 G'))

		try:
			chanctrler.low_limit = 35
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'
			
		# Test the limit restrictions.
		
		chanctrler.low_limit = Quantity('60 G')
		eq_(chanctrler.low_limit, Quantity('40 G'))
		
		chanctrler.high_limit = Quantity('30 G')
		eq_(chanctrler.high_limit, Quantity('50 G'))
		
	def testHeaters(self):
		"""
		Test the heaters.
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		# Test turning a heater on and off.
		
		chanctrler.persistent_switch_heater = 'on'
		eq_(chanctrler.persistent_switch_heater,'on')
		
		chanctrler.persistent_switch_heater = 'off'
		eq_(chanctrler.persistent_switch_heater,'off')
		
		try:
			chanctrler.persistent_switch_heater = 'something else'
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Test both heaters option.
		
		magctrler.virt_both_persistent_switch_heaters = 'on'
		eq_(magctrler.virt_both_persistent_switch_heaters, 'on')
		
		chanctrler.persistent_switch_heater = 'off'
		eq_(magctrler.virt_both_persistent_switch_heaters, 'unequal')
		
	
	def testUnits(self):
		"""
		Test the units.
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		# Test turning a heater on and off.
		
		chanctrler.units = 'A'
		eq_(chanctrler.units,'A')
		
		chanctrler.units = 'kG'
		eq_(chanctrler.units,'kG')
		
		try:
			chanctrler.units = 'T'
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		# Test both heaters option.
		
		magctrler.virt_both_units = 'A'
		eq_(magctrler.virt_both_units, 'A')
		
		chanctrler.units = 'kG'
		eq_(magctrler.virt_both_units, 'unequal')
		
		# Try setting hilim with something not in the right units, and something that is in related units.
		try:
			chanctrler.high_limit = Quantity('5 A')
		except IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'
			
		chanctrler.high_limit = Quantity('0.5 T')
		eq_(chanctrler.high_limit, Quantity('5 kG'))
		
	def testCurrentSync(self):
		"""
		Test to see if the current syncing works in a variety of circumstances.
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		# set the curs different.
		# check to see if not synced.
		chanctrler.virt_iout = Quantity('20 G')
		chanctrler.virt_sync_currents = 'start'
		chanctrler._wait_for_sweep()
		eq_(chanctrler.virt_iout,chanctrler.virt_imag)
	
	def testRounding(self):
		"""
		The model4g rounds to a nearest gaussian, and amp (??). Test this since the code relies on
		this with the sweep_to higher order functions.
		"""
		
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		chanctrler.virt_iout = Quantity('20.19 G')
		eq_(chanctrler.virt_iout, Quantity('20 G'))

	
	def testVirtIout(self):
		"""
		Test the resource virt_iout.
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		chanctrler.virt_iout = Quantity('20 G')
		eq_(chanctrler.virt_iout, Quantity('20 G'))

		try:
			chanctrler.virt_iout = 55
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'
	
	def testVirtImag(self):
		"""
		Test the resource virt_imag.
		"""
		
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		# Test a simple setting of the magnetic field.
		
		chanctrler.virt_energysave_mode = 0
		chanctrler.virt_sync_currents = 'start'
		chanctrler.persistent_switch_heater = 'on'
		chanctrler.virt_imag = Quantity('20 G')
		
		eq_(chanctrler.virt_imag, Quantity('20 G'))

		try:
			chanctrler.virt_imag = 55
		except AttributeError:
			pass
		else:
			assert False, 'Expected AttributeError.'
			
		# Energy mode 1.
		
		chanctrler.virt_energysave_mode = 1
		chanctrler.persistent_switch_heater = 'off'
		chanctrler.virt_imag = Quantity('30 G')
		
		## Check if it was set and if the heater was turned off.
		eq_(magctrler.virt_both_persistent_switch_heaters, 'off')
		eq_(chanctrler.virt_imag, Quantity('30 G')) 
		
		# Energy mode 3.
		
		chanctrler.virt_energysave_mode = 3
		chanctrler.persistent_switch_heater = 'off'
		chanctrler.virt_imag = Quantity('10 G')
		
		## Check if the heater is off.
		eq_(magctrler.virt_both_persistent_switch_heaters, 'off')
		## Check if the power is going down.
		sleep(0.5)
		eq_(chanctrler.magnet_current > chanctrler.power_supply_current, True)
		## Check if it was set properly.
		eq_(chanctrler.virt_imag, Quantity('10 G')) 
		

	def testWaitForSweep(self):
		"""
		Tests the function _wait_for_sweep()
		"""
		magctrler = self.obtain_device()
		magctrler.reset()
		chanctrler = magctrler.channels[self.channel_to_test]
		
		chanctrler.virt_iout_sweep_to = Quantity('20 G')
		chanctrler._wait_for_sweep()
		
		# Check if sweep is actually done several times.
		for _ in range(1,10):
			eq_(chanctrler.power_supply_current, Quantity('20 G'))		
		
if __name__ == '__main__':
	main()
