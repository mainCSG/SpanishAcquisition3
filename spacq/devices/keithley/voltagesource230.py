import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_unwrapped

"""
Keithley 230 Programmable Voltage Source
"""

class voltageSource230(AbstractDevice):
	"""
	Interface for the Keithly 230 Programmable Voltage Source
	"""

	allowed_I_limit = set([2, 20, 100])

	def _setup(self):
		AbstractDevice._setup(self)

		# These values are used to tune the input values according to empirical error.
		self.gain = 1.0
		self.offset = 0.0

		# Test
		self.default_Ilim = 2.0
		self.default_dwelltime = 0.01

		# Resources.
		write_only = ['voltage']
		for name in write_only:
			self.resources[name] = Resource(self, None, name)

		read_write = ['I_limit','dwell_time']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['voltage'].units = 'V'
		self.resources['I_limit'].converter = float
		self.resources['I_limit'].allowed_values = self.allowed_I_limit
		self.resources['dwell_time'].converter = float

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)
		
		# Clear the GPIB for this device
		self.device.clear()

		# Set the device to operational
		self.device.write('K0X')
		self.device.write('F1X')

	def __init__(self, vMin = -101, vMax = 101, dwellMin = 0.003, dwellMax = 0.9999, *args, **kwargs):
		"""
		Initialize the voltage source and all its ports.
		"""
		AbstractDevice.__init__(self, *args, **kwargs)
		
		self.vMin = vMin
		self.vMax = vMax
		self.dwellMin = dwellMin
		self.dwellMax = dwellMax

	@Synchronized()
	def reset(self):
		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	def calculate_voltage(self, voltage):
		"""
		Determine the value corresponding to the given voltage.
		"""

		try:
			voltage_adjusted = voltage * self.gain + self.offset
		except TypeError:
			raise ValueError('Voltage must be a number. Given: {0}'.format(voltage))

		if voltage_adjusted < self.vMin or voltage_adjusted > self.vMax:
			raise ValueError('Adjusted voltage must be within [{0}, {1}]. '
					'Given: {2}; adjusted to: {3}.'.format(self.vMin,
					self.vMax, voltage, voltage_adjusted))

		return voltage_adjusted

	@quantity_unwrapped('V')
	def set_voltage(self, voltage):
		"""
		Set the voltage on this port, as a quantity in V.
		"""

		# Left-align the bits within the value:
		# 20-bit: VVVV VVVV VVVV VVVV VVVV xxxx
		# 16-bit: VVVV VVVV VVVV VVVV xxxx xxxx
		# where the 'x's are don't-cares, so we just set them to 0 by shifting.
		resulting_voltage = self.calculate_voltage(voltage)

		# Write 24 bits to the top of the DIR: 0100 0000 xxxx xxxx xxxx xxxx xxxx xxxx
		#self.write('L1 B1 V{0:.4E}XI{1:.2E}XW{2:.3E}X'.format(resulting_voltage,self.I_limit_code,self.dwelltime))
		self.write('V{0:.4E}X'.format(resulting_voltage))
		#self.write('L1 B1 V{0:.4E}XI{1:.2E}XW{2:.3E}X'.format(resulting_voltage,0,3))

	voltage = property(fset=set_voltage)
	
	@property
	def I_limit(self):
		"""
		The current limit (in mA)
		"""
		# If no I limit has been set, use the 2mA default
		if not hasattr(self, 'currentILimit'):
			self.currentILimit = 2
			self.I_limit_code = 0

		return self.currentILimit

	@I_limit.setter
	def I_limit(self, value):
		if value not in self.allowed_I_limit:
			raise ValueError('Invalid I Limit value: {0}'.format(value))

		if value == 2:
			self.I_limit_code = 0
		elif value == 20:
			self.I_limit_code = 1
		elif value == 100:
			self.I_limit_code = 2
		self.currentILimit = value

	@property
	def dwell_time(self):
		"""
		The dwell time of the vsrc
		"""
		# If no dwell time has been set, use 10ms default
		if not hasattr(self, 'dwelltime'):
			self.dwelltime = 0.01
		return self.dwelltime
	
	@dwell_time.setter
	def dwell_time(self, value):
		if value < self.dwellMin or value > self.dwellMax:
			raise ValueError('Dwell time must be within [{0}, {1}]. Given: {2}.'.format(self.dwellMin, self.dwellMax, value))
		self.dwelltime = value

name = '230 Programmable Voltage Source'
implementation = voltageSource230
