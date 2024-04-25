import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped
from ..tools import quantity_unwrapped

"""
Keithley 2450 SourceMeasure Unit
Apply voltage/current bias and obtain measurements.
"""


class sm2450(AbstractDevice):
	"""
	Interface for Keithley 2450
	Note: Limited implementation, many features are not included
	"""

	#allowed_nplc = set([0.006, 0.02, 0.06, 0.2, 1.0, 2.0, 10.0, 100.0])

	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		read_only = ['voltageIn', 'currentIn']
		for name in read_only:
			self.resources[name] = Resource(self, name)

		write_only = ['voltageOut', 'currentOut']
		for name in write_only:
			self.resources[name] = Resource(self, None, name)

		self.resources['voltageIn'].units = 'V'
		self.resources['voltageOut'].units = 'V'
		self.resources['currentIn'].units = 'A'
		self.resources['currentOut'].units = 'A'
		
	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)

		#self.write('configure:voltage:dc')
		# TODO: Create a default setup?
	
	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	@quantity_wrapped('V')
	def voltageIn(self):
		return float(self.ask('MEAS:VOLT?'))
		
	@property
	@quantity_wrapped('A')
	def currentIn(self):
		return float(self.ask('MEAS:CURR?'))
		
	@property
	@quantity_wrapped('V')
	def voltageOut(self):
		return self.currentOutputVoltage

	@voltageOut.setter
	@quantity_unwrapped('V')
	def voltageOut(self,value):
		self.write('SOUR:VOLT {0}'.format(value))
		self.currentOutputVoltage = value
		
	@property
	@quantity_wrapped('A')
	def currentOut(self):
		return self.currentOutputCurrent
	
	@currentOut.setter
	@quantity_unwrapped('A')
	def currentOut(self,value):
		self.write('SOUR:CURR {0}'.format(value))
		self.currentOutputCurrent = value


name = 'sourceMeter 2450'
implementation = sm2450
